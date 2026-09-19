---
name: perchance-image-gen
description: >-
  Generate AI images using the reverse-engineered Perchance b7kc35yv7u backend API.
  Use when the user requests to generate, create, or render images, character portraits,
  anime art, realistic humans, or fantasy concepts using Perchance's free backend without
  API keys or sign-in. Supports 28 art styles, adult/NSFW presets, resolution control
  (512x512, 512x768, 768x512, 768x768), CFG guidance scale, and deterministic seed reproduction.
---

# Perchance Image Generation Skill (b7kc35yv7u)

This skill allows agents to programmatically generate and save AI images using the reverse-engineered Perchance backend API and style templates from `perchance.org/b7kc35yv7u`.

---

## When to Use This Skill

Activate this skill when:
1. The user asks to generate images using Perchance or the `b7kc35yv7u` generator.
2. The user requests text-to-image generation without requiring external paid API keys (OpenAI, Midjourney, Stability AI).
3. The user wants to generate character portraits, artistic illustrations, anime figures, or realistic humans using specific art styles.

---

## Available Execution Methods

Agents can generate images using either the CLI wrapper or by directly executing a Python snippet.

### Method 1: CLI Execution via `run_command` (Recommended)

Run `perchance_client.py` located in `C:\ANTI\webgenimg\perchance_client.py`:

```powershell
python C:\ANTI\webgenimg\perchance_client.py --prompt "<PROMPT>" --style "<STYLE>" --shape "<RESOLUTION>" --out "<OUTPUT_PATH>"
```

#### Common Examples:

- **Realistic Portrait (512x768)**:
  ```powershell
  python C:\ANTI\webgenimg\perchance_client.py --prompt "portrait of a cyberpunk detective standing in neon rain" --style "Realistic humans" --shape "512x768" --out "detective.jpeg"
  ```

- **Fantasy / Cinematic Landscape (768x512)**:
  ```powershell
  python C:\ANTI\webgenimg\perchance_client.py --prompt "ancient elven city carved into waterfalls at sunset, volumetric god rays" --style "Realistic images" --shape "768x512" --out "elven_city.jpeg"
  ```

- **Adult / NSFW Style Preset**:
  ```powershell
  python C:\ANTI\webgenimg\perchance_client.py --prompt "portrait of a noble sorceress in arcane sanctum" --style "NSFW - Realistic" --adult --shape "512x768" --out "sorceress.jpeg"
  ```

- **Reproduce Exact Seed**:
  ```powershell
  python C:\ANTI\webgenimg\perchance_client.py --prompt "majestic phoenix rising from flames" --seed 1068771166 --out "phoenix.jpeg"
  ```

---

### Method 2: Python Script Import

```python
import sys
sys.path.append(r"C:\ANTI\webgenimg")
from perchance_client import PerchanceClient

client = PerchanceClient()

# Generate image
result = client.generate(
    prompt="portrait of a medieval knight in gothic armor",
    negative_prompt="blurry, distorted, low quality",
    art_style="Realistic images",
    shape="512x768",      # '512x512', '512x768', '768x512', or '768x768'
    guidance_scale=7.0,   # Range: 1.0 to 30.0 (default 7.0)
    seed=-1,              # -1 for random, or specific integer
    adult_mode=False
)

# Download and save
client.download_image(result, "knight.jpeg")
print(f"Image saved. Seed: {result.seed}, ImageID: {result.image_id}")
```

---

## Parameter Specifications

| Parameter | Options / Type | Description |
| :--- | :--- | :--- |
| `prompt` | string (required) | Core text description. Use parentheses `(text)` to add 1.1x weight, `((text))` for 1.2x. |
| `negative_prompt` | string (optional) | Artifacts to suppress (e.g. `bad anatomy, blurry, extra limbs, low quality`). |
| `art_style` | string | One of the 28 pre-built styles (see list below). Default: `"Realistic images"`. |
| `art_style_mix`| string | Secondary style mix. Use `"Not Mix"` or `"NSFW"` to append `, nsfw`. |
| `adult_mode` | boolean | If `true`, injects mature tags and strips anti-NSFW negatives. |
| `shape` | string | `"512x512"` (Square), `"512x768"` (Portrait), `"768x512"` (Landscape), `"768x768"` (Large Square). |
| `guidance_scale` | float | CFG Scale (`1.0` - `30.0`). Default is `7.0`. |
| `seed` | integer | Random seed (`-1` = randomized). Specific number replicates identical image. |

---

## Complete List of 28 Art Styles

### Standard Styles:
- `Realistic images` (High-definition, 4K/8K, sharp focus)
- `Realistic humans` (Detailed human features, skin textures, anatomically accurate)
- `Realistic Human Generator` (Natural raw portrait, film grain, candid)
- `No style` (Raw prompt passed directly to model)
- `Anti-NSFW` (Forces SFW filtering)
- `League of Legends` (Digital concept art, WLOP inspired)
- `MTG Card` (Fantasy trading card illustration)
- `Final Fantasy` (CGI video game 3D style)
- `Dragonball` (Anime style)
- `Star Wars Character` / `Star Wars Battle` (Cinematic space aesthetic)
- `Lego`, `Terraria`, `Webcore`, `Skittles`, `ENA`, `Undertale?`
- `Jester`, `Ninja`, `Neko (Catgirl)`, `American Girl`, `Random Girl 1`, `Random Girl 2`

### Adult (+18) Styles:
- `NSFW - Realistic` (Photorealistic adult aesthetic, volumetric rim lighting)
- `NSFW - Anime` (High-detail anime aesthetic with fluid motion)
- `NSFW - Realistic (Stronger)` (Weighted `(((nsfw)))`)
- `NSFW - Anime (Stronger)` (Weighted `(((nsfw)))`)
- `NSFW Painted Anime` (Painterly anime aesthetic, Pixiv/WLOP inspired)

---

## Web App and MCP Integration

- **Web Application**: Launch `python C:\ANTI\webgenimg\web_app.py` to start the interactive browser interface on `http://127.0.0.1:8000`.
- **MCP Server**: Launch `python C:\ANTI\webgenimg\perchance_mcp.py` to expose `generate_perchance_image` tool directly to MCP clients.
