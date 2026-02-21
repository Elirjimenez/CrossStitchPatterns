from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.application.ports.image_resizer import ImageResizer
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Pattern, PatternGrid
from app.domain.services.color_matching import select_palette
from app.domain.services.confetti import reduce_confetti
from app.domain.services.image_mode_detector import DeterministicHeuristicImageModeDetector

_mode_detector = DeterministicHeuristicImageModeDetector()

_RESAMPLING_FOR_MODE = {
    "pixel_art": "nearest",
    "drawing": "bilinear",
    "photo": "lanczos",
}


@dataclass(frozen=True)
class ConvertImageRequest:
    image_data: bytes
    num_colors: int
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    min_frequency_pct: float = 1.0
    processing_mode: str = "auto"  # "auto" | "photo" | "drawing" | "pixel_art"


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

        # Determine effective processing mode
        mode = request.processing_mode
        if mode == "auto":
            thumbnail = self._image_resizer.load_and_resize(
                request.image_data, 64, 64, resampling="nearest"
            )
            mode = _mode_detector.detect(thumbnail).mode

        resampling = _RESAMPLING_FOR_MODE.get(mode, "lanczos")
        min_freq = 0.0 if mode == "pixel_art" else request.min_frequency_pct

        pixels = self._image_resizer.load_and_resize(
            request.image_data, target_width, target_height, resampling=resampling,
        )

        palette, index_grid, dmc_list = select_palette(
            pixels, request.num_colors, min_freq
        )
        if mode != "pixel_art":
            index_grid = reduce_confetti(index_grid)

        grid = PatternGrid(
            width=target_width,
            height=target_height,
            cells=index_grid,
        )

        pattern = Pattern(grid=grid, palette=palette)
        return ConvertImageResult(pattern=pattern, dmc_colors=dmc_list)
