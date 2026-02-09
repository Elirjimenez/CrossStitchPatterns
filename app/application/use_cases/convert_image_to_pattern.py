from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.application.ports.image_resizer import ImageResizer
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Pattern, PatternGrid
from app.domain.services.color_matching import select_palette
from app.domain.services.confetti import reduce_confetti


@dataclass(frozen=True)
class ConvertImageRequest:
    image_data: bytes
    num_colors: int
    target_width: Optional[int] = None
    target_height: Optional[int] = None


@dataclass(frozen=True)
class ConvertImageResult:
    pattern: Pattern
    dmc_colors: List[DmcColor]


class ConvertImageToPattern:
    def __init__(self, image_resizer: ImageResizer):
        self._image_resizer = image_resizer

    def execute(self, request: ConvertImageRequest) -> ConvertImageResult:
        if request.target_width is None or request.target_height is None:
            img_w, img_h = self._image_resizer.get_image_size(request.image_data)
            target_width = request.target_width or img_w
            target_height = request.target_height or img_h
        else:
            target_width = request.target_width
            target_height = request.target_height

        pixels = self._image_resizer.load_and_resize(
            request.image_data, target_width, target_height
        )

        palette, index_grid, dmc_list = select_palette(pixels, request.num_colors)
        index_grid = reduce_confetti(index_grid)

        grid = PatternGrid(
            width=target_width,
            height=target_height,
            cells=index_grid,
        )

        pattern = Pattern(grid=grid, palette=palette)
        return ConvertImageResult(pattern=pattern, dmc_colors=dmc_list)
