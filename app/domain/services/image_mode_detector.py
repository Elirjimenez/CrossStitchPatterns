"""Deterministic image mode detection for cross-stitch pattern generation.

Classifies an input image as 'photo', 'drawing', or 'pixel_art' using
four lightweight heuristics.  No ML is involved — results are fully
deterministic for a given pixel grid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Protocol

from app.domain.model.pattern import RGB

# -----------------------------------------------------------------
# Types
# -----------------------------------------------------------------

ImageMode = Literal["photo", "drawing", "pixel_art"]

# Thresholds (sum of absolute per-channel differences, range 0–765)
_EDGE_THRESHOLD: int = 60   # diff above this → edge pixel
_FLAT_THRESHOLD: int = 15   # diff below this → flat adjacent pair

# Classification boundaries
_PIXEL_ART_MAX_COLORS: int = 64
_DRAWING_MAX_COLORS: int = 1000
_DRAWING_MIN_EDGE_DENSITY: float = 0.3


# -----------------------------------------------------------------
# Result dataclass
# -----------------------------------------------------------------


@dataclass(frozen=True)
class ImageModeDetection:
    """Result of mode detection, including debug heuristic scores."""

    mode: ImageMode
    unique_color_count: int
    edge_density: float    # fraction of pixels classified as edge [0, 1]
    avg_neighbor_diff: float  # mean sum-of-abs diff between adjacent pixels
    flat_ratio: float      # fraction of adjacent pairs with near-zero diff [0, 1]


# -----------------------------------------------------------------
# Protocol (port)
# -----------------------------------------------------------------


class ImageModeDetector(Protocol):
    """Port: classifies an image's visual style from its pixel grid."""

    def detect(self, pixels: List[List[RGB]]) -> ImageModeDetection:
        """Classify the image represented by *pixels*.

        Args:
            pixels: 2-D list of (R, G, B) tuples.  Typically a small
                    thumbnail (≤ 64×64) for performance.

        Returns:
            ImageModeDetection with the detected mode and raw scores.
        """
        ...


# -----------------------------------------------------------------
# Default implementation
# -----------------------------------------------------------------


class DeterministicHeuristicImageModeDetector:
    """Classifies images using four deterministic pixel-level heuristics.

    Classification rules (applied to the supplied pixel grid, usually a
    small thumbnail):

    1. unique_color_count ≤ 64  →  **pixel_art**
       (very few distinct colours)

    2. edge_density > 0.3  AND  64 < unique_color_count < 1000
       →  **drawing**
       (sharp outlines, moderate colour variety)

    3. Everything else  →  **photo**
       (smooth gradients, large colour space)
    """

    def detect(self, pixels: List[List[RGB]]) -> ImageModeDetection:
        height = len(pixels)
        width = len(pixels[0]) if height else 0

        if height == 0 or width == 0:
            return ImageModeDetection(
                mode="photo",
                unique_color_count=0,
                edge_density=0.0,
                avg_neighbor_diff=0.0,
                flat_ratio=0.0,
            )

        # ------------------------------------------------------------------
        # Heuristic 1: unique colour count
        # ------------------------------------------------------------------
        unique_colors: set[RGB] = set()
        for row in pixels:
            unique_colors.update(row)
        unique_color_count = len(unique_colors)

        # ------------------------------------------------------------------
        # Heuristics 2–4: edge density, avg neighbour diff, flat ratio
        # Iterate once, checking horizontal and vertical neighbours.
        # ------------------------------------------------------------------
        edge_count: int = 0
        diff_sum: float = 0.0
        total_pairs: int = 0
        flat_pairs: int = 0

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[y][x]
                max_diff: int = 0

                # Horizontal neighbour (right)
                if x + 1 < width:
                    nr, ng, nb = pixels[y][x + 1]
                    d = abs(r - nr) + abs(g - ng) + abs(b - nb)
                    diff_sum += d
                    total_pairs += 1
                    if d < _FLAT_THRESHOLD:
                        flat_pairs += 1
                    if d > max_diff:
                        max_diff = d

                # Vertical neighbour (below)
                if y + 1 < height:
                    nr, ng, nb = pixels[y + 1][x]
                    d = abs(r - nr) + abs(g - ng) + abs(b - nb)
                    diff_sum += d
                    total_pairs += 1
                    if d < _FLAT_THRESHOLD:
                        flat_pairs += 1
                    if d > max_diff:
                        max_diff = d

                if max_diff > _EDGE_THRESHOLD:
                    edge_count += 1

        total_pixels = height * width
        edge_density = edge_count / total_pixels
        avg_neighbor_diff = diff_sum / total_pairs if total_pairs > 0 else 0.0
        flat_ratio = flat_pairs / total_pairs if total_pairs > 0 else 0.0

        # ------------------------------------------------------------------
        # Classification
        # ------------------------------------------------------------------
        if unique_color_count <= _PIXEL_ART_MAX_COLORS:
            mode: ImageMode = "pixel_art"
        elif edge_density > _DRAWING_MIN_EDGE_DENSITY and unique_color_count < _DRAWING_MAX_COLORS:
            mode = "drawing"
        else:
            mode = "photo"

        return ImageModeDetection(
            mode=mode,
            unique_color_count=unique_color_count,
            edge_density=edge_density,
            avg_neighbor_diff=avg_neighbor_diff,
            flat_ratio=flat_ratio,
        )
