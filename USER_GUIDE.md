# Perchance Image Generator (b7kc35yv7u) — Complete User Guide

Welcome to the comprehensive guide for the **Perchance b7kc35yv7u Replicant Application**. This suite allows you to generate AI images using Perchance's backend GPU infrastructure without limitations, accounts, or API keys.

---

## 📑 Table of Contents
1. [Overview & Features](#1-overview--features)
2. [Running the Web Application (Interactive UI)](#2-running-the-web-application-interactive-ui)
3. [Using the Command Line Interface (CLI)](#3-using-the-command-line-interface-cli)
4. [Using the Python SDK / Library](#4-using-the-python-sdk--library)
5. [Using the MCP Server (Model Context Protocol)](#5-using-the-mcp-server-model-context-protocol)
6. [Settings, Parameters & Workflows](#6-settings-parameters--workflows)
7. [Adult Mode (+18) & NSFW Presets](#7-adult-mode-18--nsfw-presets)
8. [Prompt Engineering Tips](#8-prompt-engineering-tips)
9. [Troubleshooting & FAQ](#9-troubleshooting--faq)

---

## 1. Overview & Features

This application reverse-engineers the generator at `https://perchance.org/b7kc35yv7u` created by community developer *9gin*. It replicates:
- **Direct backend communication** via tokenless session authentication (`/api/verifyUser` + `/api/generate`).
- **All 28 Art Style presets** extracted directly from the generator's source code.
- **Adult (+18) mode toggle** with NSFW-specific presets (*NSFW - Realistic*, *NSFW - Anime*, *NSFW Painted Anime*) and quick modifiers.
- **Aspect Ratio / Resolution control**: Square (`512x512`), Portrait (`512x768`), Landscape (`768x512`), Large Square (`768x768`).
- **Guidance Scale (CFG)** slider (1.0 to 30.0).
- **Deterministic Seed replication** (`-1` for random).
- **Interactive local gallery** with real-time download buttons, prompt copy, and sensitive content blur toggles.

---

## 2. Running the Web Application (Interactive UI)

The Web Application provides a modern dark-themed interface mirroring `b7kc35yv7u`.

### How to Start:
1. Open PowerShell or terminal in the project directory:
   ```powershell
   cd C:\ANTI\webgenimg
   python web_app.py
   ```
2. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000
   ```

### Web UI Controls:
- **🔞 Adult Mode (+18) Toggle**: Located at the top right header. When turned **ON**, it unlocks the adult art style presets (*NSFW - Realistic*, *NSFW - Anime*, etc.), shows quick adult modifier pills, and removes content blur.
- **🎲 Random Button**: Inserts a curated high-detail prompt template.
- **🎨 Art Style Select**: Choose from 28 styles. When Adult Mode is enabled, adult styles appear grouped at the top.
- **🎨 Art Style Mixing**: Combine a secondary style or select `NSFW` to inject `, nsfw`.
- **🖼 Resolution Select**: Choose between `Square (512x512)`, `Portrait (512x768)`, `Landscape (768x512)`, or `Large Square (768x768)`.
- **✒️ CFG Scale**: Adjust prompt adherence (default `7.0`).
- **🔢 Batch Count**: Generate 1 to 4 images concurrently.
- **🖼 Gallery**: Displays generated images with prompt details, seed numbers, download buttons, and 18+ blur toggles.

---

## 3. Using the Command Line Interface (CLI)

You can generate images directly from your terminal using `perchance_client.py`:

```powershell
# Basic SFW generation
python perchance_client.py -p "cyberpunk ronin samurai in rain" -s "Realistic images" -o "samurai.jpeg"

# Portrait aspect ratio (512x768)
python perchance_client.py -p "portrait of a blonde Roman noblewoman" -s "Realistic humans" --shape "512x768" -o "noblewoman.jpeg"

# Adult (+18) generation
python perchance_client.py -p "gorgeous noble sorceress in arcane sanctum" -s "NSFW - Realistic" --adult --shape "512x768" -o "sorceress.jpeg"

# Specific seed reproduction
python perchance_client.py -p "majestic phoenix" --seed 1068771166 -o "phoenix.jpeg"

# List all 28 available art styles
python perchance_client.py --list-styles
```

### CLI Options Reference:
| Flag | Long Argument | Default | Description |
| :--- | :--- | :--- | :--- |
| `-p` | `--prompt` | `""` | Image description prompt |
| `-n` | `--negative` | `""` | Negative prompt |
| `-s` | `--style` | `"Realistic images"` | Name of art style preset |
| | `--mix` | `"Not Mix"` | Secondary style mix |
| `-a` | `--adult` | `False` | Enable Adult (+18) mode |
| | `--shape` | `"512x512"` | `512x512`, `512x768`, `768x512`, `768x768` |
| `-g` | `--guidance` | `7.0` | Guidance / CFG scale (`1.0` - `30.0`) |
| | `--seed` | `-1` | Seed (`-1` for random) |
| `-o` | `--out` | `"output.jpeg"` | Output file path |
| | `--list-styles` | — | Print all 28 styles and exit |

---

## 4. Using the Python SDK / Library

You can integrate image generation into your own Python scripts:

```python
from perchance_client import PerchanceClient

client = PerchanceClient()

# Generate an image
result = client.generate(
    prompt="portrait of an elven archer in a magical forest",
    negative_prompt="blurry, distorted",
    art_style="Realistic images",
    shape="512x768",
    guidance_scale=7.0,
    seed=-1,
    adult_mode=False
)

print(f"Generated Image ID: {result.image_id}")
print(f"Seed: {result.seed}")
print(f"Flagged Sensitive: {result.maybe_nsfw}")

# Save image to file
client.download_image(result, "elven_archer.jpeg")
```

---

## 5. Using the MCP Server (Model Context Protocol)

The MCP server allows AI assistants (Antigravity, Claude Desktop, Cursor, etc.) to call the generator as a native tool.

### Starting the Server:
```powershell
python perchance_mcp.py
```

### Configuring in AI Clients:
Add this to your MCP configuration file (e.g. `claude_desktop_config.json` or Antigravity's `mcp_config.json`):

```json
{
  "mcpServers": {
    "perchance-image-generator": {
      "command": "python",
      "args": ["C:/ANTI/webgenimg/perchance_mcp.py"]
    }
  }
}
```

### Available MCP Tools:
1. **`generate_perchance_image`**:
   - `prompt`: Text description
   - `negative_prompt`: Things to avoid
   - `art_style`: Preset name (e.g. `"Realistic images"`, `"NSFW - Realistic"`)
   - `art_style_mix`: Secondary mix (e.g. `"Not Mix"`, `"NSFW"`)
   - `adult_mode`: Boolean flag
   - `shape`: `"512x512"`, `"512x768"`, `"768x512"`, `"768x768"`
   - `guidance_scale`: Float (default `7.0`)
   - `seed`: Int (`-1` for random)
   - `output_filename`: Optional filename
2. **`list_available_styles`**: Returns all 28 supported style names.
3. **`get_style_info`**: Inspects prompt & negative templates for any style.

---

## 6. Settings, Parameters & Workflows

### How Prompts are Constructed:
`b7kc35yv7u` uses a composition workflow:
```
Final Prompt = [artStyle.prompt(description)], [artStyleMix.prompt], [extra_modifiers]
Final Negative = [artStyle.negative(negative)], [artStyleMix.negative]
```
- When you select an art style, your description is inserted into the style's master prompt template.
- Negative prompts are combined automatically to filter out distortions, bad anatomy, and low-quality artifacts.

### Supported Resolutions:
- **`512x512`** (Square): Standard square frame, fast generation.
- **`512x768`** (Portrait): Ideal for characters, portraits, human figures.
- **`768x512`** (Landscape): Ideal for panoramic scenery, environments, battles.
- **`768x768`** (Large Square): High-detail square format.

### Guidance Scale (CFG):
- **`1.0 - 4.0`**: Loose, creative interpretation.
- **`7.0` (Default)**: Sweet spot. High prompt fidelity with sharp details.
- **`12.0 - 20.0`**: Strict prompt adherence. May become over-saturated if prompt is brief.

---

## 7. Adult Mode (+18) & NSFW Presets

In `b7kc35yv7u`, the adult options are represented by specific style recipes:

1. **`NSFW - Realistic`**:
   - Injects realistic photography terms, volumetric lighting, anatomically correct indicators, and fine skin/eye detailing.
   - Applies an extensive negative prompt blocking 3D CGI, anime sketches, and malformed limbs.
2. **`NSFW - Anime`**:
   - Injects hyper-anime styling, fluid motion, dramatic lighting, and ArtStation trending tags.
3. **`NSFW - Realistic (Stronger)` / `NSFW - Anime (Stronger)`**:
   - Uses weighted syntax `(((nsfw)))` for higher emphasis.
4. **`NSFW Painted Anime`**:
   - Injects painterly digital art aesthetic (Pixiv, Kantoku, Atey Ghailan, WLOP styles).
5. **Art Style Mix = `NSFW`**:
   - Appends `, nsfw` to the final prompt.

> **Note on Content Filtering**: The Perchance backend API **does not block** adult image generation. It flags images with `"maybeNsfw": true`, and the front-end applies a client-side `#contentGuardEl` blur. In our web application, you can reveal sensitive images by clicking "Click to View" or pressing "👁 Reveal NSFW Blur".

---

## 8. Prompt Engineering Tips

1. **Weighting with Parentheses**:
   - `red dress` = normal weight
   - `(red dress)` = 1.1x emphasis
   - `((red dress))` = 1.2x emphasis
   - `(((red dress:1.4)))` = 1.4x strong emphasis
2. **Random Variation `{choice1|choice2}`**:
   - Perchance supports brace-delimited choices: e.g. `{blonde|dark|red} hair`, `{blue|green} eyes`.
3. **Negative Prompting**:
   - If human figures have mutated hands or extra limbs, add: `bad hands, extra fingers, missing fingers, extra limbs, bad anatomy, deformed limbs`.

---

## 9. Troubleshooting & FAQ

- **Q: Why do some images take longer to generate?**
  - Perchance utilizes a shared GPU pool. Generation times range between 3 to 15 seconds depending on server load.
- **Q: How do I recreate the exact same image?**
  - Note the `seed` number from the gallery or CLI output. Pass `--seed <number>` with the identical prompt, style, resolution, and guidance scale.
- **Q: Does this require any API key or subscription?**
  - No. Perchance's image generation is completely free and public.
