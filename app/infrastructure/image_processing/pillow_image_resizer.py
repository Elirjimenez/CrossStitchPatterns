from __future__ import annotations

import io
from typing import List, Tuple
from PIL import Image, UnidentifiedImageError

from app.application.ports.image_resizer import ImageResizer
from app.domain.model.pattern import RGB

_RESAMPLING_MAP = {
    "lanczos": Image.Resampling.LANCZOS,
    "bilinear": Image.Resampling.BILINEAR,
    "nearest": Image.Resampling.NEAREST,
}


class PillowImageResizer(ImageResizer):
    def get_image_size(self, image_bytes: bytes) -> Tuple[int, int]:
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except (UnidentifiedImageError, IOError, OSError) as e:
            raise ValueError(f"Invalid image data: {e}")
        return img.size  # (width, height)

    def load_and_resize(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        resampling: str = "lanczos",
    ) -> List[List[RGB]]:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be > 0")
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except (UnidentifiedImageError, IOError, OSError) as e:
            raise ValueError(f"Invalid image data: {e}")

        img = img.convert("RGB")
        filter_ = _RESAMPLING_MAP.get(resampling, Image.Resampling.LANCZOS)
        img = img.resize((width, height), filter_)

        pixels: List[List[RGB]] = []
        for y in range(height):
            row: List[RGB] = []
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                row.append((r, g, b))
            pixels.append(row)
        return pixels
