"""Unit tests for DeterministicHeuristicImageModeDetector.

Tests use synthetic pixel grids designed to trigger each mode classification
deterministically without reading from disk or using ML.
"""

from __future__ import annotations

import math
from typing import List

from app.domain.model.pattern import RGB
from app.domain.services.image_mode_detector import (
    DeterministicHeuristicImageModeDetector,
    ImageModeDetection,
)


# ---------------------------------------------------------------------------
# Synthetic image helpers
# ---------------------------------------------------------------------------


def _solid_block_pixels(colors: List[RGB], block_size: int = 8) -> List[List[RGB]]:
    """Grid of solid colour blocks — pixel-art style.

    Example: 4 colours, block_size=8 → 16×16 image with 4 blocks.
    """
    n = len(colors)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    result: List[List[RGB]] = []
    for by in range(rows):
        for _ in range(block_size):
            row: List[RGB] = []
            for bx in range(cols):
                idx = by * cols + bx
                color = colors[idx] if idx < n else colors[-1]
                row.extend([color] * block_size)
            result.append(row)
    return result


def _gradient_pixels(size: int = 64) -> List[List[RGB]]:
    """Smooth 2-channel gradient — photo-like.

    Produces many unique colours and very low edge density.
    """
    return [
        [(int(x * 255 / (size - 1)), int(y * 200 / (size - 1)), 100) for x in range(size)]
        for y in range(size)
    ]


def _drawing_pixels(size: int = 32) -> List[List[RGB]]:
    """Gradient background with dense horizontal lines — drawing-like.

    Every 3rd row is a black line, giving edge_density > 0.3.
    Background gradient gives >64 and <1000 unique colours.
    """
    pixels: List[List[RGB]] = []
    for y in range(size):
        row: List[RGB] = []
        for x in range(size):
            if y % 3 == 0:
                row.append((0, 0, 0))
            else:
                r = 180 + int(x * 0.6)
                g = 160 + int(y * 0.6)
                row.append((r, g, 120))
        pixels.append(row)
    return pixels


# ---------------------------------------------------------------------------
# Pixel-art detection
# ---------------------------------------------------------------------------


class TestDetectPixelArt:
    def test_solid_blocks_classified_as_pixel_art(self):
        """4-colour solid blocks → unique_color_count ≤ 64 → pixel_art."""
        colors: List[RGB] = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        pixels = _solid_block_pixels(colors, block_size=8)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.mode == "pixel_art"

    def test_unique_color_count_matches_palette(self):
        """Result reports the exact number of unique colours used."""
        colors: List[RGB] = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        pixels = _solid_block_pixels(colors, block_size=8)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.unique_color_count == 4

    def test_single_colour_image_is_pixel_art(self):
        """All-red image has 1 unique colour → pixel_art."""
        pixels: List[List[RGB]] = [[(255, 0, 0)] * 16 for _ in range(16)]
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.mode == "pixel_art"

    def test_exactly_64_colours_is_pixel_art(self):
        """64 unique colours is the upper boundary for pixel_art."""
        # 64 distinct colours arranged in a single flat row
        colors: List[RGB] = [(i * 4, 0, 0) for i in range(64)]
        pixels: List[List[RGB]] = [colors]
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.mode == "pixel_art"

    def test_65_colours_is_not_pixel_art_by_count_alone(self):
        """65 unique colours alone does not trigger pixel_art (no flat_ratio check)."""
        colors: List[RGB] = [(i * 3, 0, 0) for i in range(65)]
        # Without high flat_ratio, falls through to photo or drawing
        pixels: List[List[RGB]] = [colors]
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.mode != "pixel_art"


# ---------------------------------------------------------------------------
# Photo detection
# ---------------------------------------------------------------------------


class TestDetectPhoto:
    def test_smooth_gradient_classified_as_photo(self):
        """Smooth gradient → many unique colours, low edge density → photo."""
        pixels = _gradient_pixels(size=64)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.mode == "photo"

    def test_gradient_has_many_unique_colours(self):
        """Gradient image reports more than 64 unique colours."""
        pixels = _gradient_pixels(size=64)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.unique_color_count > 64

    def test_avg_neighbour_diff_is_low_for_smooth_gradient(self):
        """Adjacent pixels in a smooth gradient differ by very little."""
        pixels = _gradient_pixels(size=64)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.avg_neighbor_diff < 20.0

    def test_edge_density_is_low_for_smooth_gradient(self):
        """Smooth gradient has few pixels classified as edges."""
        pixels = _gradient_pixels(size=64)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.edge_density < 0.1


# ---------------------------------------------------------------------------
# Drawing detection
# ---------------------------------------------------------------------------


class TestDetectDrawing:
    def test_dense_lines_on_gradient_classified_as_drawing(self):
        """Gradient bg + dense sharp lines → edge_density > 0.3 → drawing."""
        pixels = _drawing_pixels(size=32)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.mode == "drawing"

    def test_drawing_has_high_edge_density(self):
        """Drawing image with dense lines has edge_density > 0.3."""
        pixels = _drawing_pixels(size=32)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.edge_density > 0.3

    def test_drawing_unique_colour_count_is_moderate(self):
        """Drawing image has more than 64 but fewer than 1000 unique colours."""
        pixels = _drawing_pixels(size=32)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert 64 < result.unique_color_count < 1000


# ---------------------------------------------------------------------------
# Return type and field validity
# ---------------------------------------------------------------------------


class TestDetectionResult:
    def test_returns_image_mode_detection_instance(self):
        """detect() always returns an ImageModeDetection dataclass."""
        pixels: List[List[RGB]] = [[(128, 128, 128)] * 10 for _ in range(10)]
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert isinstance(result, ImageModeDetection)

    def test_mode_is_one_of_three_valid_values(self):
        """mode field is always one of the three valid string literals."""
        pixels: List[List[RGB]] = [[(128, 128, 128)] * 10 for _ in range(10)]
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.mode in ("photo", "drawing", "pixel_art")

    def test_edge_density_is_between_0_and_1(self):
        """edge_density is a valid fraction [0, 1]."""
        pixels = _gradient_pixels(size=32)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert 0.0 <= result.edge_density <= 1.0

    def test_flat_ratio_is_between_0_and_1(self):
        """flat_ratio is a valid fraction [0, 1]."""
        pixels = _gradient_pixels(size=32)
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert 0.0 <= result.flat_ratio <= 1.0

    def test_avg_neighbour_diff_is_non_negative(self):
        """avg_neighbor_diff is always ≥ 0."""
        pixels: List[List[RGB]] = [[(0, 0, 0)] * 5 for _ in range(5)]
        result = DeterministicHeuristicImageModeDetector().detect(pixels)
        assert result.avg_neighbor_diff >= 0.0

    def test_empty_pixels_returns_photo_default(self):
        """Empty pixel list returns a safe default (photo)."""
        result = DeterministicHeuristicImageModeDetector().detect([])
        assert result.mode == "photo"
        assert result.unique_color_count == 0
        assert result.edge_density == 0.0
