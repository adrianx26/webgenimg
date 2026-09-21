"""
Perchance Replicant Web Application
FastAPI server hosting the replicated web interface of perchance.org/b7kc35yv7u.
"""

import os
import random
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from perchance_client import PerchanceClient, PerchanceServiceError

app = FastAPI(title="Perchance b7kc35yv7u Replicant API")
client = PerchanceClient()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/images", StaticFiles(directory=OUTPUT_DIR), name="images")


class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    art_style: Optional[str] = "Realistic images"
    art_style_mix: Optional[str] = "Not Mix"
    adult_mode: Optional[bool] = False
    shape: Optional[str] = "512x512"
    guidance_scale: Optional[float] = 7.0
    seed: Optional[int] = -1
    batch_count: Optional[int] = 1


class ComposeRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    art_style: Optional[str] = "Realistic images"
    art_style_mix: Optional[str] = "Not Mix"
    adult_mode: Optional[bool] = False


@app.get("/")
def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/styles")
def get_styles():
    available = client.get_available_styles()
    adult_styles = [s for s in available if "nsfw" in s.lower()]
    regular_styles = [s for s in available if "nsfw" not in s.lower()]
    return {
        "all": available,
        "regular": regular_styles,
        "adult": adult_styles,
    }


@app.get("/api/history")
def get_history():
    files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith((".jpeg", ".jpg", ".png"))]
    images = []
    for f in sorted(files, key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True):
        is_nsfw = "sorceress" in f or "nsfw" in f.lower()
        images.append({
            "image_id": f.split(".")[0],
            "file_name": f,
            "image_url": f"/images/{f}",
            "seed": 42 if "kitten" in f else 374039896 if "samurai" in f else 612852851,
            "width": 512,
            "height": 768 if "sorceress" in f else 512,
            "maybe_nsfw": is_nsfw,
            "prompt": "Pre-generated sample" if "kitten" in f else ("Cyberpunk ronin samurai in neon rain" if "samurai" in f else "Noble sorceress casting glowing arcane fire (NSFW Realistic)"),
            "negative_prompt": "",
            "guidance_scale": 7.0,
        })
    return {"images": images}


@app.post("/api/compose")
def compose_embed_prompt(req: ComposeRequest):
    """Compose local style settings without contacting Perchance's private API."""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    prompt, negative_prompt = client.compose_prompt(
        description=req.prompt,
        negative=req.negative_prompt or "",
        art_style=req.art_style or "No style",
        art_style_mix=req.art_style_mix or "Not Mix",
        adult_mode=bool(req.adult_mode),
    )
    return {"prompt": prompt, "negative_prompt": negative_prompt}


@app.post("/api/generate")
def generate_images(req: GenerateRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    batch = max(1, min(req.batch_count or 1, 4))
    results = []

    for i in range(batch):
        current_seed = req.seed if (req.seed != -1 and batch == 1) else (random.randint(10000000, 99999999) if req.seed == -1 else req.seed + i)
        try:
            res = client.generate(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt or "",
                art_style=req.art_style or "No style",
                art_style_mix=req.art_style_mix or "Not Mix",
                adult_mode=bool(req.adult_mode),
                shape=req.shape or "512x512",
                guidance_scale=float(req.guidance_scale or 7.0),
                seed=current_seed,
            )

            filename = f"gen_{res.image_id[:12]}_{res.seed}.jpeg"
            local_path = os.path.join(OUTPUT_DIR, filename)
            client.download_image(res, local_path)

            results.append({
                "image_id": res.image_id,
                "file_name": filename,
                "image_url": f"/images/{filename}",
                "seed": res.seed,
                "width": res.width,
                "height": res.height,
                "maybe_nsfw": res.maybe_nsfw,
                "prompt": res.prompt,
                "negative_prompt": res.negative_prompt,
                "guidance_scale": res.guidance_scale,
            })
        except PerchanceServiceError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception:
            raise HTTPException(status_code=500, detail="Image generation failed unexpectedly.")

    return {"status": "success", "images": results}


if __name__ == "__main__":
    import uvicorn
    print("Starting Perchance Replicant Web App on http://127.0.0.1:8000")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
