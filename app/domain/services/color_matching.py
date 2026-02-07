"""
Color matching service for mapping RGB colors to DMC embroidery thread colors.

Uses CIE LAB color space with Delta E (CIE76) for perceptually accurate matching.
Pure Python implementation — no external dependencies beyond the standard library.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from collections import Counter

from app.domain.data.dmc_colors import DMC_COLORS, DmcColor
from app.domain.model.pattern import Palette, RGB

# Cache of pre-computed LAB values for all DMC colors
_dmc_lab_cache: Optional[List[Tuple[DmcColor, Tuple[float, float, float]]]] = None


def rgb_to_lab(rgb: RGB) -> Tuple[float, float, float]:
    """Convert an sRGB color to CIE LAB color space.

    Uses the standard sRGB -> XYZ -> LAB conversion with D65 illuminant.
    """
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

    # sRGB to linear RGB
    r = _srgb_to_linear(r)
    g = _srgb_to_linear(g)
    b = _srgb_to_linear(b)

    # Linear RGB to XYZ (D65 illuminant)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    # XYZ to LAB (D65 reference white)
    x /= 0.95047
    y /= 1.00000
    z /= 1.08883

    x = _lab_f(x)
    y = _lab_f(y)
    z = _lab_f(z)

    L = 116.0 * y - 16.0
    a = 500.0 * (x - y)
    b_val = 200.0 * (y - z)

    return (L, a, b_val)


def _srgb_to_linear(c: float) -> float:
    """Convert sRGB component to linear RGB."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _lab_f(t: float) -> float:
    """CIE LAB transfer function."""
    if t > (6.0 / 29.0) ** 3:
        return t ** (1.0 / 3.0)
    return t / (3.0 * (6.0 / 29.0) ** 2) + 4.0 / 29.0


def delta_e(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """CIE76 Delta E — Euclidean distance in LAB color space."""
    return math.sqrt((lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2)


def _get_dmc_lab_table() -> List[Tuple[DmcColor, Tuple[float, float, float]]]:
    """Return pre-computed LAB values for all DMC colors (cached)."""
    global _dmc_lab_cache
    if _dmc_lab_cache is None:
        _dmc_lab_cache = [
            (color, rgb_to_lab((color.r, color.g, color.b))) for color in DMC_COLORS.values()
        ]
    return _dmc_lab_cache


def find_nearest_dmc(rgb: RGB) -> DmcColor:
    """Find the DMC color that is perceptually closest to the given RGB color."""
    target_lab = rgb_to_lab(rgb)
    table = _get_dmc_lab_table()

    best_color = table[0][0]
    best_dist = delta_e(target_lab, table[0][1])

    for dmc_color, dmc_lab in table[1:]:
        dist = delta_e(target_lab, dmc_lab)
        if dist < best_dist:
            best_dist = dist
            best_color = dmc_color

    return best_color


def select_palette(
    pixels: List[List[RGB]], num_colors: int
) -> Tuple[Palette, List[List[int]], List[DmcColor]]:
    """Map a 2D pixel grid to a DMC palette with at most num_colors colors.

    Returns:
        palette: Palette with the selected DMC RGB colors
        grid: 2D list of palette indices (same dimensions as input)
        dmc_list: ordered list of DmcColor objects matching palette indices
    """
    # Map every pixel to its nearest DMC color
    dmc_grid: List[List[DmcColor]] = []
    frequency: Counter[str] = Counter()
    for row in pixels:
        dmc_row = []
        for pixel in row:
            dmc = find_nearest_dmc(pixel)
            dmc_row.append(dmc)
            frequency[dmc.number] += 1
        dmc_grid.append(dmc_row)

    # Pick top N most frequent DMC colors
    top_numbers = [number for number, _ in frequency.most_common(num_colors)]
    selected = {n: DMC_COLORS[n] for n in top_numbers}
    dmc_list = [selected[n] for n in top_numbers]

    # Pre-compute LAB for selected colors for remapping
    selected_lab = [(dmc, rgb_to_lab((dmc.r, dmc.g, dmc.b))) for dmc in dmc_list]
    number_to_index = {dmc.number: i for i, dmc in enumerate(dmc_list)}

    # Build index grid, remapping non-selected colors to nearest selected
    index_grid: List[List[int]] = []
    for dmc_row in dmc_grid:
        index_row = []
        for dmc in dmc_row:
            if dmc.number in number_to_index:
                index_row.append(number_to_index[dmc.number])
            else:
                # Remap to nearest selected color
                target_lab = rgb_to_lab((dmc.r, dmc.g, dmc.b))
                best_idx = 0
                best_dist = delta_e(target_lab, selected_lab[0][1])
                for i, (_, lab) in enumerate(selected_lab[1:], 1):
                    dist = delta_e(target_lab, lab)
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i
                index_row.append(best_idx)
        index_grid.append(index_row)

    palette = Palette(colors=[(dmc.r, dmc.g, dmc.b) for dmc in dmc_list])
    return palette, index_grid, dmc_list
