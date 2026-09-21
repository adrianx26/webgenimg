"""
Perchance Client Library for Image Generation
Reverse-engineered from https://perchance.org/b7kc35yv7u (Fast Free AI Animation / Image Generator)
"""

import json
import os
import random
import re
import base64
import shutil
import time
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import parse_qs, urlparse
import httpx

BASE_URL = "https://image-generation.perchance.org/api"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/153.0.0.0 Safari/537.36"
)

# Load extracted styles from b7kc35yv7u
STYLES_FILE = os.path.join(os.path.dirname(__file__), "extracted_styles.json")

import unicodedata

def _normalize_key(name: str) -> str:
    norm = unicodedata.normalize('NFKD', name.strip())
    # Standardize 'No style'
    if norm.lower() in ("no style", "none"):
        return "No style"
    return norm


class GenerationResult:
    def __init__(self, data: Dict[str, Any], download_url: str):
        self.status: str = data.get("status", "")
        self.image_id: str = data.get("imageId", "")
        self.file_extension: str = data.get("fileExtension", "jpeg")
        self.seed: int = data.get("seed", -1)
        self.prompt: str = data.get("prompt", "")
        self.negative_prompt: str = data.get("negativePrompt", "")
        self.width: int = data.get("width", 512)
        self.height: int = data.get("height", 512)
        self.guidance_scale: float = data.get("guidanceScale", 7.0)
        self.maybe_nsfw: bool = data.get("maybeNsfw", False)
        self.image_download_url: str = download_url
        self.raw_data: Dict[str, Any] = data

    def __repr__(self) -> str:
        return (
            f"<GenerationResult id={self.image_id} {self.width}x{self.height} "
            f"seed={self.seed} nsfw={self.maybe_nsfw}>"
        )


class PerchanceServiceError(RuntimeError):
    """An actionable error returned by Perchance's image service."""

    pass


class PerchanceClient:
    def __init__(
        self,
        channel: str = "ai-text-to-image-generator",
        sub_channel: str = "public",
        generator_name: str = "ai-image-generator",
    ):
        self.channel = channel
        self.sub_channel = sub_channel
        self.generator_name = generator_name
        self.user_key: Optional[str] = None
        self.last_verified: float = 0
        self.styles: Dict[str, Dict[str, str]] = self._load_styles()

        self.client = httpx.Client(
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Referer": "https://image-generation.perchance.org/",
                "Origin": "https://image-generation.perchance.org",
                "Accept": "*/*",
            },
            timeout=90.0,
        )

    @staticmethod
    def _get_json(response: httpx.Response, operation: str) -> Dict[str, Any]:
        """Decode a Perchance response and turn gateway pages into useful errors."""
        content_type = response.headers.get("content-type", "")
        if response.status_code in (403, 429) or "text/html" in content_type:
            raise PerchanceServiceError(
                f"Perchance blocked {operation} (HTTP {response.status_code}). "
                "The service requires a normal browser session; this unofficial client "
                "cannot complete a Cloudflare challenge."
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise PerchanceServiceError(
                f"Perchance returned a non-JSON response while attempting {operation} "
                f"(HTTP {response.status_code})."
            ) from exc
        if not isinstance(data, dict):
            raise PerchanceServiceError(
                f"Perchance returned an unexpected response while attempting {operation}."
            )
        return data

    def _load_styles(self) -> Dict[str, Dict[str, str]]:
        if os.path.exists(STYLES_FILE):
            with open(STYLES_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            cleaned = {}
            for k, v in raw.items():
                norm_key = _normalize_key(k)
                cleaned[norm_key] = v
                cleaned[k] = v  # keep original too
            return cleaned
        return {}

    def get_available_styles(self) -> List[str]:
        # Return unique normalized names
        seen = set()
        res = []
        for k in self.styles:
            norm = _normalize_key(k)
            if norm not in seen:
                seen.add(norm)
                res.append(norm)
        return sorted(res)

    def verify_user(self, force: bool = False) -> str:
        """Verify user key with Perchance backend API."""
        now = time.time()
        if self.user_key and not force and (now - self.last_verified < 1800):
            return self.user_key

        url = f"{BASE_URL}/verifyUser?thread=0&__cacheBust={random.random()}"
        res = self.client.get(url)
        data = self._get_json(res, "user verification")
        if data.get("status") in ("success", "already_verified"):
            self.user_key = data.get("userKey")
            self.last_verified = now
            return self.user_key
        if data.get("status") == "client_update_required":
            raise PerchanceServiceError(
                "Perchance rejected this client as outdated. Its browser integration "
                "has changed, and the direct unofficial API flow needs an update."
            )
        raise PerchanceServiceError(f"User verification failed: {data}")

    @staticmethod
    def _browser_executable() -> Optional[str]:
        configured = os.environ.get("PERCHANCE_CHROME_PATH")
        if configured:
            return configured
        candidates = [
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
            shutil.which("chrome"),
            shutil.which("google-chrome"),
        ]
        return next((path for path in candidates if path and os.path.exists(path)), None)

    def _generate_in_browser(
        self,
        prompt: str,
        negative_prompt: str,
        art_style: str,
        art_style_mix: str,
        adult_mode: bool,
        shape: str,
        guidance_scale: float,
        seed: int,
        sub_channel: Optional[str],
        extra_modifiers: Optional[List[str]],
    ) -> GenerationResult:
        """Use a real Chromium context when Perchance requires Turnstile verification."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise PerchanceServiceError(
                "Perchance requires browser verification. Install the Playwright dependency "
                "and a Chrome/Chromium browser, then retry."
            ) from exc

        final_prompt, final_neg = self.compose_prompt(
            description=prompt,
            negative=negative_prompt,
            art_style=art_style,
            art_style_mix=art_style_mix,
            adult_mode=adult_mode,
            extra_modifiers=extra_modifiers,
        )
        res_map = {
            "portrait": "512x768",
            "square": "512x512",
            "landscape": "768x512",
            "large_square": "768x768",
            "portrait(512x768px)": "512x768",
            "square(512x512px)": "512x512",
            "landscape(768x512px)": "768x512",
            "512x512": "512x512",
            "512x768": "512x768",
            "768x512": "768x512",
            "768x768": "768x768",
        }
        resolution = res_map.get(shape.lower().strip(), "512x512")
        target_sub_channel = sub_channel or ("nsfw" if adult_mode else self.sub_channel)
        key_pattern = re.compile(r"userKey=([a-fA-F0-9]{64})")

        executable = self._browser_executable()
        if not executable:
            raise PerchanceServiceError(
                "Perchance requires browser verification, but no Chrome executable was found. "
                "Set PERCHANCE_CHROME_PATH to a full Chrome/Chromium executable."
            )

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=executable,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(user_agent=DEFAULT_USER_AGENT)
            page = context.new_page()
            captured_key: List[str] = []
            captured_generate_urls: List[str] = []
            generated_request_finished = False

            def capture_key(request: Any) -> None:
                match = key_pattern.search(request.url)
                if match and not captured_key:
                    captured_key.append(match.group(1))
                if "/api/generate?" in request.url:
                    captured_generate_urls.append(request.url)

            page.on("request", capture_key)

            def capture_response(response: Any) -> None:
                nonlocal generated_request_finished
                if "/api/generate?" in response.url:
                    generated_request_finished = True

            page.on("response", capture_response)
            try:
                page.goto("https://perchance.org/b7kc35yv7u", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                # New browser sessions show a content-preferences gate before
                # the generator iframe is created.
                warning_button = page.get_by_text("I am over 18 - Show Content", exact=False)
                if warning_button.count():
                    page.evaluate(
                        """() => {
                            const button = document.getElementById("showContentBtn");
                            if (button) button.click();
                        }"""
                    )
                    page.wait_for_timeout(5000)

                if not captured_key:
                    for frame in page.frames:
                        buttons = frame.locator("button")
                        for index in range(buttons.count()):
                            button = buttons.nth(index)
                            if "generate" in button.inner_text(timeout=2000).lower():
                                button.click(timeout=10000)
                                break
                        if captured_key:
                            break
                deadline = time.time() + 45
                while not captured_key and time.time() < deadline:
                    page.wait_for_timeout(500)
                if not captured_key:
                    raise PerchanceServiceError(
                        "Perchance browser verification did not provide an access key. "
                        "The site may be blocked by a browser challenge."
                    )

                user_key = captured_key[0]
                if not captured_generate_urls:
                    raise PerchanceServiceError(
                        "Perchance browser verification returned an access key but no "
                        "generation contract."
                    )
                deadline = time.time() + 180
                while not generated_request_finished and time.time() < deadline:
                    page.wait_for_timeout(1000)
                if not generated_request_finished:
                    raise PerchanceServiceError(
                        "Perchance did not finish its initial browser request before "
                        "the generation window expired."
                    )
                generate_query = parse_qs(urlparse(captured_generate_urls[-1]).query)
                ad_access_code = generate_query.get("adAccessCode", [""])[0]
                if not ad_access_code:
                    raise PerchanceServiceError(
                        "Perchance browser verification did not provide an ad access code."
                    )
                page.goto(
                    "https://image-generation.perchance.org/api/verifyUser"
                    "?thread=0&__cacheBust=" + str(random.random()),
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(3000)
                request_id = f"aiImageCompletion{random.randint(10000000, 99999999)}"
                data = page.evaluate(
                    """
                    async ({userKey, requestId, adAccessCode, prompt, negativePrompt,
                            seed, resolution, guidanceScale, channel, subChannel}) => {
                        const url = `https://image-generation.perchance.org/api/generate`
                            + `?userKey=${encodeURIComponent(userKey)}`
                            + `&requestId=${encodeURIComponent(requestId)}`
                            + `&adAccessCode=${encodeURIComponent(adAccessCode)}`
                            + `&__cacheBust=${Math.random()}`;
                        const response = await fetch(url, {
                            method: "POST",
                            headers: {"Content-Type": "application/json"},
                            body: JSON.stringify({
                                generatorName: "ai-image-generator",
                                prompt, negativePrompt, seed, resolution,
                                guidanceScale, channel, subChannel, userKey,
                                adAccessCode, requestId
                            })
                        });
                        return await response.json();
                    }
                    """,
                    {
                        "userKey": user_key,
                        "requestId": request_id,
                        "adAccessCode": ad_access_code,
                        "prompt": final_prompt,
                        "negativePrompt": final_neg,
                        "seed": int(seed),
                        "resolution": resolution,
                        "guidanceScale": float(guidance_scale),
                        "channel": "b7kc35yv7u",
                        "subChannel": target_sub_channel,
                    },
                )
                if not isinstance(data, dict) or data.get("status") != "success":
                    raise PerchanceServiceError(f"Generation failed in browser: {data}")

                download_path = data.get("imageDownloadUrl", "")
                download_url = (
                    f"https://image-generation.perchance.org{download_path}"
                    if download_path.startswith("/")
                    else download_path
                )
                result = GenerationResult(data, download_url)
                encoded_image = page.evaluate(
                    """
                    async (url) => {
                        const response = await fetch(url);
                        if (!response.ok) throw new Error(`HTTP ${response.status}`);
                        const bytes = new Uint8Array(await response.arrayBuffer());
                        let binary = "";
                        for (const byte of bytes) binary += String.fromCharCode(byte);
                        return btoa(binary);
                    }
                    """,
                    download_url,
                )
                result._image_bytes = base64.b64decode(encoded_image)
                return result
            finally:
                browser.close()

    def compose_prompt(
        self,
        description: str,
        negative: str = "",
        art_style: str = "No style",
        art_style_mix: str = "Not Mix",
        adult_mode: bool = False,
        extra_modifiers: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """
        Implements b7kc35yv7u workflow for synthesizing prompt & negative prompt.
        """
        # Resolve main art style
        style_key = _normalize_key(art_style)
        style_obj = self.styles.get(style_key, self.styles.get(art_style, None))

        if not style_obj or style_key in ("No style", "None", ""):
            prompt = description
            neg = negative
        else:
            style_p = style_obj.get("prompt", "[input.description]")
            style_n = style_obj.get("negative", "[input.negative]")
            prompt = style_p.replace("[input.description]", description)
            neg = style_n.replace("[input.negative]", negative)

        # Adult (+18) mode handling
        if adult_mode:
            # If user didn't explicitly pick an NSFW style, append nsfw keywords
            if "nsfw" not in prompt.lower():
                prompt = f"{prompt}, (nsfw:1.2), mature, highly detailed"
            if "nsfw" in neg.lower():
                # Remove anti-nsfw filters from negative prompt
                neg = re.sub(r'\b(nsfw|nudity|inappropriate|18\+ content)\b', '', neg, flags=re.I)

        # Resolve mixing style
        mix_key = _normalize_key(art_style_mix)
        if mix_key == "NSFW":
            prompt = f"{prompt}, nsfw"
        elif mix_key not in ("Not Mix", "None", ""):
            mix_obj = self.styles.get(mix_key, self.styles.get(art_style_mix, None))
            if mix_obj:
                mix_p = mix_obj.get("prompt", "").replace("[input.description]", "")
                mix_n = mix_obj.get("negative", "").replace("[input.negative]", "")
                if mix_p:
                    prompt = f"{prompt}, {mix_p}".strip(", ")
                if mix_n:
                    neg = f"{neg}, {mix_n}".strip(", ")

        # Append optional extra modifiers
        if extra_modifiers:
            mod_str = ", ".join(extra_modifiers)
            prompt = f"{prompt}, {mod_str}".strip(", ")

        # Clean up double commas/whitespace
        prompt = re.sub(r',\s*,+', ',', prompt).strip(', ')
        neg = re.sub(r',\s*,+', ',', neg).strip(', ')

        return prompt, neg

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        art_style: str = "No style",
        art_style_mix: str = "Not Mix",
        adult_mode: bool = False,
        shape: str = "Square(512x512px)",
        guidance_scale: float = 7.0,
        seed: int = -1,
        sub_channel: Optional[str] = None,
        extra_modifiers: Optional[List[str]] = None,
    ) -> GenerationResult:
        """
        Generate image using the Perchance b7kc35yv7u workflow.
        """
        try:
            user_key = self.verify_user()
        except PerchanceServiceError as exc:
            if "client as outdated" in str(exc) or "Cloudflare challenge" in str(exc):
                return self._generate_in_browser(
                    prompt, negative_prompt, art_style, art_style_mix, adult_mode,
                    shape, guidance_scale, seed, sub_channel, extra_modifiers,
                )
            raise

        # Parse resolution
        res_map = {
            "portrait": "512x768",
            "square": "512x512",
            "landscape": "768x512",
            "large_square": "768x768",
            "portrait(512x768px)": "512x768",
            "square(512x512px)": "512x512",
            "landscape(768x512px)": "768x512",
            "512x512": "512x512",
            "512x768": "512x768",
            "768x512": "768x512",
            "768x768": "768x768",
        }
        res_val = res_map.get(shape.lower().strip(), "512x512")

        # Compose workflow prompt & negative prompt
        final_prompt, final_neg = self.compose_prompt(
            description=prompt,
            negative=negative_prompt,
            art_style=art_style,
            art_style_mix=art_style_mix,
            adult_mode=adult_mode,
            extra_modifiers=extra_modifiers,
        )

        req_id = f"aiImageCompletion{random.randint(10000000, 99999999)}"
        url = (
            f"{BASE_URL}/generate?"
            f"userKey={user_key}&"
            f"requestId={req_id}&"
            f"__cacheBust={random.random()}"
        )

        target_sub_channel = sub_channel or ("nsfw" if adult_mode else self.sub_channel)

        body = {
            # Current Perchance clients identify the hosted image generator separately
            # from the public generation channel.
            "generatorName": self.generator_name,
            "prompt": final_prompt,
            "negativePrompt": final_neg,
            "seed": int(seed),
            "resolution": res_val,
            "guidanceScale": float(guidance_scale),
            "channel": self.channel,
            "subChannel": target_sub_channel,
            "userKey": user_key,
            "requestId": req_id,
        }

        # Submit request
        res = self.client.post(url, json=body)
        data = self._get_json(res, "image generation")

        if data.get("status") == "invalid_key":
            try:
                user_key = self.verify_user(force=True)
            except PerchanceServiceError as exc:
                if "client as outdated" in str(exc) or "Cloudflare challenge" in str(exc):
                    return self._generate_in_browser(
                        prompt, negative_prompt, art_style, art_style_mix, adult_mode,
                        shape, guidance_scale, seed, sub_channel, extra_modifiers,
                    )
                raise
            body["userKey"] = user_key
            url = f"{BASE_URL}/generate?userKey={user_key}&requestId={req_id}&__cacheBust={random.random()}"
            res = self.client.post(url, json=body)
            data = self._get_json(res, "image generation")

        if data.get("status") != "success":
            raise PerchanceServiceError(f"Generation failed: {data}")

        download_path = data.get("imageDownloadUrl", "")
        if download_path.startswith("/"):
            download_url = f"https://image-generation.perchance.org{download_path}"
        else:
            download_url = download_path

        return GenerationResult(data, download_url)

    def download_image(self, result_or_url: Any, output_path: str) -> str:
        """Download generated image bytes and write to disk."""
        image_bytes = getattr(result_or_url, "_image_bytes", None)
        if image_bytes is not None:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            return output_path

        if isinstance(result_or_url, GenerationResult):
            url = result_or_url.image_download_url
        else:
            url = str(result_or_url)

        res = self.client.get(url)
        if res.status_code != 200:
            raise PerchanceServiceError(f"Image download failed with HTTP {res.status_code}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(res.content)
        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Perchance Image Generator CLI (b7kc35yv7u replicant)")
    parser.add_argument("--prompt", "-p", default="", help="Image description / prompt")
    parser.add_argument("--negative", "-n", default="", help="Negative prompt")
    parser.add_argument("--style", "-s", default="Realistic images", help="Art style name")
    parser.add_argument("--mix", default="Not Mix", help="Art style mixing")
    parser.add_argument("--adult", "-a", action="store_true", help="Enable adult (+18) mode")
    parser.add_argument("--shape", default="512x512", choices=["512x512", "512x768", "768x512", "768x768"])
    parser.add_argument("--guidance", "-g", type=float, default=7.0, help="Guidance scale (1-30)")
    parser.add_argument("--seed", type=int, default=-1, help="Seed (-1 for random)")
    parser.add_argument("--out", "-o", default="output.jpeg", help="Output file path")
    parser.add_argument("--list-styles", action="store_true", help="List all available styles")

    args = parser.parse_args()
    client = PerchanceClient()

    if args.list_styles:
        print("Available styles:")
        for s in client.get_available_styles():
            print(f"  - {s}")
        return

    if not args.prompt:
        parser.error("--prompt / -p is required when generating an image.")

    print(f"[*] Connecting to Perchance API...")
    print(f"[*] Prompt: '{args.prompt}' (Style: {args.style}, Adult: {args.adult}, Shape: {args.shape})")
    result = client.generate(
        prompt=args.prompt,
        negative_prompt=args.negative,
        art_style=args.style,
        art_style_mix=args.mix,
        adult_mode=args.adult,
        shape=args.shape,
        guidance_scale=args.guidance,
        seed=args.seed,
    )
    print(f"[+] Success! Image ID: {result.image_id}, Seed: {result.seed}, NSFW flag: {result.maybe_nsfw}")
    print(f"[*] Downloading image to {args.out}...")
    client.download_image(result, args.out)
    print(f"[+] Done! Image saved to {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
