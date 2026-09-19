"""
Perchance MCP Server (Model Context Protocol)
Exposes Perchance b7kc35yv7u image generation capabilities as MCP tools.
Can be integrated into Antigravity, Claude Desktop, Cursor, or any MCP-compatible environment.
"""

import os
from typing import Optional
from fastmcp import FastMCP
from perchance_client import PerchanceClient

mcp = FastMCP("perchance-image-generator")
client = PerchanceClient()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@mcp.tool()
def list_available_styles() -> list[str]:
    """
    List all available art styles extracted from perchance.org/b7kc35yv7u.
    Includes both standard styles (Realistic images, MTG Card, etc.) and
    adult (+18) styles (NSFW - Realistic, NSFW - Anime, NSFW Painted Anime, etc.).
    """
    return client.get_available_styles()


@mcp.tool()
def get_style_info(style_name: str) -> dict:
    """
    Get the prompt and negative prompt templates for a specific art style.
    
    Args:
        style_name: Name of the art style (e.g. 'Realistic images', 'NSFW - Realistic')
    """
    styles = client.styles
    from perchance_client import _normalize_key
    norm = _normalize_key(style_name)
    style_obj = styles.get(norm, styles.get(style_name))
    if not style_obj:
        return {"error": f"Style '{style_name}' not found."}
    return {
        "name": norm,
        "prompt_template": style_obj.get("prompt", ""),
        "negative_template": style_obj.get("negative", ""),
    }


@mcp.tool()
def generate_perchance_image(
    prompt: str,
    negative_prompt: str = "",
    art_style: str = "Realistic images",
    art_style_mix: str = "Not Mix",
    adult_mode: bool = False,
    shape: str = "512x512",
    guidance_scale: float = 7.0,
    seed: int = -1,
    output_filename: Optional[str] = None,
) -> dict:
    """
    Generate an image using the Perchance backend API replicating the b7kc35yv7u workflow.
    
    Args:
        prompt: Description of the image you want to generate.
        negative_prompt: Elements to exclude from the image.
        art_style: Art style preset (e.g. 'Realistic images', 'NSFW - Realistic', 'NSFW - Anime', 'No style').
        art_style_mix: Secondary art style mix ('Not Mix', 'NSFW', or any style name).
        adult_mode: Whether to enable adult (+18) mode. Injects mature tags and relaxes NSFW filtering.
        shape: Resolution format: '512x512' (Square), '512x768' (Portrait), '768x512' (Landscape), or '768x768'.
        guidance_scale: Prompt alignment / CFG scale from 1.0 to 30.0 (default: 7.0).
        seed: Random seed (-1 for random). Reusing a seed reproduces the exact image.
        output_filename: Optional custom file name to save the image (saved in generated_images/).
        
    Returns:
        Dictionary containing imageId, local_path, seed, width, height, maybe_nsfw, and download_url.
    """
    result = client.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        art_style=art_style,
        art_style_mix=art_style_mix,
        adult_mode=adult_mode,
        shape=shape,
        guidance_scale=guidance_scale,
        seed=seed,
    )

    filename = output_filename or f"img_{result.image_id[:12]}_{result.seed}.jpeg"
    if not filename.lower().endswith((".jpeg", ".jpg", ".png")):
        filename += ".jpeg"
    
    local_path = os.path.join(OUTPUT_DIR, filename)
    client.download_image(result, local_path)

    return {
        "status": "success",
        "image_id": result.image_id,
        "seed": result.seed,
        "width": result.width,
        "height": result.height,
        "maybe_nsfw": result.maybe_nsfw,
        "local_file_path": os.path.abspath(local_path),
        "remote_download_url": result.image_download_url,
        "composed_prompt": result.prompt,
        "composed_negative_prompt": result.negative_prompt,
    }


if __name__ == "__main__":
    mcp.run()
