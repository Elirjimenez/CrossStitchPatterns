from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.application.ports.image_resizer import ImageResizer
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Pattern, PatternGrid
from app.domain.services.color_matching import select_palette


@dataclass(frozen=True)
class ConvertImageRequest:
    image_data: bytes
    target_width: int
    target_height: int
    num_colors: int


@dataclass(frozen=True)
class ConvertImageResult:
    pattern: Pattern
    dmc_colors: List[DmcColor]


class ConvertImageToPattern:
    def __init__(self, image_resizer: ImageResizer):
        self._image_resizer = image_resizer

    def execute(self, request: ConvertImageRequest) -> ConvertImageResult:
        pixels = self._image_resizer.load_and_resize(
            request.image_data, request.target_width, request.target_height
        )

        palette, index_grid, dmc_list = select_palette(pixels, request.num_colors)

        grid = PatternGrid(
            width=request.target_width,
            height=request.target_height,
            cells=index_grid,
        )

        pattern = Pattern(grid=grid, palette=palette)
        return ConvertImageResult(pattern=pattern, dmc_colors=dmc_list)
