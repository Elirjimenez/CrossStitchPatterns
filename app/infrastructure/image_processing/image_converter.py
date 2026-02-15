"""
Image processing adapter using Pillow.

Handles image loading, resizing, and pixel extraction.
"""

from __future__ import annotations

import io
from typing import List

from PIL import Image, UnidentifiedImageError

from app.domain.model.pattern import RGB


def load_and_resize(image_bytes: bytes, width: int, height: int) -> List[List[RGB]]:
    """Load an image from bytes, resize it, and return a 2D pixel grid.

    Args:
        image_bytes: Raw image data (PNG, JPEG, etc.)
        width: Target width in pixels (stitches)
        height: Target height in pixels (stitches)

    Returns:
        2D list of RGB tuples: pixels[y][x] -> (r, g, b)

    Raises:
        ValueError: If image data is invalid or dimensions are non-positive.
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be > 0")

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except (UnidentifiedImageError, IOError, OSError) as e:
        raise ValueError(f"Invalid image data: {e}")

    img = img.convert("RGB")
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    pixels: List[List[RGB]] = []
    for y in range(height):
        row: List[RGB] = []
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            row.append((r, g, b))
        pixels.append(row)

    return pixels
