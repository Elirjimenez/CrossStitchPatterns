from __future__ import annotations

import io
from typing import List
from PIL import Image

from app.application.ports.image_resizer import ImageResizer
from app.domain.model.pattern import RGB

class PillowImageResizer(ImageResizer):
    def load_and_resize(self, image_bytes: bytes, width: int, height: int) -> List[List[RGB]]:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be > 0")
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception:
            raise ValueError("Invalid image data")

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
