"""
Color matching service for mapping RGB colors to DMC embroidery thread colors.

Uses CIE LAB color space with Delta E (CIE76) for perceptually accurate matching.
The hot path (select_palette) is vectorised with NumPy for practical performance;
the scalar helpers (rgb_to_lab, find_nearest_dmc) are kept for single-pixel use.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import List, Optional, Tuple

import numpy as np

from app.domain.data.dmc_colors import DMC_COLORS, DmcColor
from app.domain.model.pattern import Palette, RGB

# ---------------------------------------------------------------------------
# Module-level caches
# ---------------------------------------------------------------------------

# Scalar cache: list of (DmcColor, LAB tuple) — used by find_nearest_dmc
_dmc_lab_cache: Optional[List[Tuple[DmcColor, Tuple[float, float, float]]]] = None

# NumPy cache: ordered list of DmcColor + corresponding (N_dmc, 3) LAB array
_dmc_colors_ordered: Optional[List[DmcColor]] = None
_dmc_lab_array: Optional[np.ndarray] = None  # shape (N_dmc, 3), float64


# ---------------------------------------------------------------------------
# Scalar colour-space helpers (public — used by tests and find_nearest_dmc)
# ---------------------------------------------------------------------------

def rgb_to_lab(rgb: RGB) -> Tuple[float, float, float]:
    """Convert an sRGB color to CIE LAB color space.

    Uses the standard sRGB -> XYZ -> LAB conversion with D65 illuminant.
    """
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

    r = _srgb_to_linear(r)
    g = _srgb_to_linear(g)
    b = _srgb_to_linear(b)

    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

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
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _lab_f(t: float) -> float:
    if t > (6.0 / 29.0) ** 3:
        return t ** (1.0 / 3.0)
    return t / (3.0 * (6.0 / 29.0) ** 2) + 4.0 / 29.0


def delta_e(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """CIE76 Delta E — Euclidean distance in LAB color space."""
    return math.sqrt(
        (lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2
    )


def _get_dmc_lab_table() -> List[Tuple[DmcColor, Tuple[float, float, float]]]:
    """Return pre-computed scalar LAB table (cached)."""
    global _dmc_lab_cache
    if _dmc_lab_cache is None:
        _dmc_lab_cache = [
            (color, rgb_to_lab((color.r, color.g, color.b))) for color in DMC_COLORS.values()
        ]
    return _dmc_lab_cache


def find_nearest_dmc(rgb: RGB) -> DmcColor:
    """Find the DMC color perceptually closest to the given RGB color (scalar)."""
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


# ---------------------------------------------------------------------------
# Vectorised NumPy batch matcher
# ---------------------------------------------------------------------------

def _get_dmc_numpy_cache() -> Tuple[List[DmcColor], np.ndarray]:
    """Return (ordered DmcColor list, LAB array of shape (N_dmc, 3)), cached."""
    global _dmc_colors_ordered, _dmc_lab_array
    if _dmc_lab_array is None:
        colors = list(DMC_COLORS.values())
        _dmc_colors_ordered = colors
        labs = np.array(
            [rgb_to_lab((c.r, c.g, c.b)) for c in colors], dtype=np.float64
        )  # (N_dmc, 3)
        _dmc_lab_array = labs
    return _dmc_colors_ordered, _dmc_lab_array  # type: ignore[return-value]


def _rgb_array_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Vectorised sRGB -> CIE LAB conversion.

    Args:
        rgb: uint8 array of shape (N, 3)

    Returns:
        float64 array of shape (N, 3) with [L, a, b] columns
    """
    f = rgb.astype(np.float64) / 255.0

    # sRGB -> linear RGB
    linear = np.where(f <= 0.04045, f / 12.92, ((f + 0.055) / 1.055) ** 2.4)

    # Linear RGB -> XYZ (D65)
    M = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ], dtype=np.float64)
    xyz = linear @ M.T  # (N, 3)

    # Normalise by D65 white point
    xyz[:, 0] /= 0.95047
    xyz[:, 2] /= 1.08883

    # f function (vectorised)
    delta = (6.0 / 29.0) ** 3
    slope = 1.0 / (3.0 * (6.0 / 29.0) ** 2)
    xyz_f = np.where(xyz > delta, xyz ** (1.0 / 3.0), slope * xyz + 4.0 / 29.0)

    L = 116.0 * xyz_f[:, 1] - 16.0
    a = 500.0 * (xyz_f[:, 0] - xyz_f[:, 1])
    b = 200.0 * (xyz_f[:, 1] - xyz_f[:, 2])

    return np.stack([L, a, b], axis=1)  # (N, 3)


def find_nearest_dmc_batch(rgb_pixels: np.ndarray) -> np.ndarray:
    """Return the index into DMC_COLORS (ordered list) nearest to each pixel.

    Args:
        rgb_pixels: uint8 array of shape (N, 3)

    Returns:
        int64 array of shape (N,) — index into list(DMC_COLORS.values())
    """
    _, dmc_labs = _get_dmc_numpy_cache()  # (N_dmc, 3)
    pixel_labs = _rgb_array_to_lab(rgb_pixels)  # (N, 3)

    # Squared Delta E: (N, N_dmc) via broadcasting
    diff = pixel_labs[:, np.newaxis, :] - dmc_labs[np.newaxis, :, :]  # (N, N_dmc, 3)
    dist_sq = np.sum(diff ** 2, axis=2)  # (N, N_dmc)

    return np.argmin(dist_sq, axis=1)  # (N,)


# ---------------------------------------------------------------------------
# select_palette — vectorised hot path
# ---------------------------------------------------------------------------

def select_palette(
    pixels: List[List[RGB]], num_colors: int, min_frequency_pct: float = 1.0
) -> Tuple[Palette, List[List[int]], List[DmcColor]]:
    """Map a 2D pixel grid to a DMC palette with at most num_colors colors.

    num_colors is a maximum — the palette may be smaller if the image contains
    fewer distinct colors or the frequency threshold removes rare ones.

    min_frequency_pct: DMC colors covering fewer than this percentage of total
    pixels are treated as noise/artifacts and merged into the nearest surviving color.
    Set to 0.0 to disable filtering. Default is 1.0 (1%).

    Returns:
        palette:  Palette with the selected DMC RGB colors
        grid:     2D list of palette indices (same shape as input)
        dmc_list: ordered DmcColor list matching palette indices
    """
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    total_pixels = height * width

    dmc_colors_ordered, _ = _get_dmc_numpy_cache()

    # ------------------------------------------------------------------
    # Step 1: Deduplicate unique RGB values and run the batch matcher
    # only once per unique colour.
    # ------------------------------------------------------------------
    flat_rgb = np.array(
        [pixel for row in pixels for pixel in row], dtype=np.uint8
    )  # (total_pixels, 3)

    unique_rgb, inverse = np.unique(flat_rgb, axis=0, return_inverse=True)
    # unique_rgb: (U, 3),  inverse: (total_pixels,) — maps each pixel to its unique index

    dmc_indices_for_unique = find_nearest_dmc_batch(unique_rgb)  # (U,)

    # Expand back to the full flat grid
    flat_dmc_indices = dmc_indices_for_unique[inverse]  # (total_pixels,)

    # ------------------------------------------------------------------
    # Step 2: Count frequency of each matched DMC colour
    # ------------------------------------------------------------------
    frequency: Counter[int] = Counter(flat_dmc_indices.tolist())

    # ------------------------------------------------------------------
    # Step 3: Apply frequency threshold
    # ------------------------------------------------------------------
    if min_frequency_pct > 0.0 and total_pixels > 0:
        min_count = total_pixels * min_frequency_pct / 100.0
        frequency = Counter({k: v for k, v in frequency.items() if v >= min_count})

    # ------------------------------------------------------------------
    # Step 4: Select top N most frequent DMC colours
    # ------------------------------------------------------------------
    actual_colors = min(num_colors, len(frequency))
    top_dmc_indices = [idx for idx, _ in frequency.most_common(actual_colors)]
    dmc_list = [dmc_colors_ordered[i] for i in top_dmc_indices]

    # Map dmc index → palette position for the surviving colours
    dmc_idx_to_palette = {dmc_idx: palette_pos for palette_pos, dmc_idx in enumerate(top_dmc_indices)}

    # ------------------------------------------------------------------
    # Step 5: Remap non-surviving pixels to nearest surviving colour
    # using the same vectorised approach.
    # ------------------------------------------------------------------
    # Build LAB array for selected palette colours only
    selected_rgb = np.array(
        [[dmc.r, dmc.g, dmc.b] for dmc in dmc_list], dtype=np.uint8
    )  # (K, 3)
    selected_lab = _rgb_array_to_lab(selected_rgb)  # (K, 3)

    # For each unique DMC index, compute its palette index
    unique_dmc_indices = np.unique(flat_dmc_indices)
    dmc_to_palette_map = np.empty(len(dmc_colors_ordered), dtype=np.int32)

    # Pixels whose DMC colour is not in the top-N need remapping
    survivor_set = set(top_dmc_indices)
    fallback_candidates_rgb = []
    fallback_candidates_dmc_idx = []

    for dmc_idx in unique_dmc_indices.tolist():
        if dmc_idx in dmc_idx_to_palette:
            dmc_to_palette_map[dmc_idx] = dmc_idx_to_palette[dmc_idx]
        else:
            c = dmc_colors_ordered[dmc_idx]
            fallback_candidates_rgb.append([c.r, c.g, c.b])
            fallback_candidates_dmc_idx.append(dmc_idx)

    if fallback_candidates_rgb:
        fb_arr = np.array(fallback_candidates_rgb, dtype=np.uint8)
        fb_labs = _rgb_array_to_lab(fb_arr)  # (F, 3)
        diff = fb_labs[:, np.newaxis, :] - selected_lab[np.newaxis, :, :]
        nearest_palette = np.argmin(np.sum(diff ** 2, axis=2), axis=1)
        for dmc_idx, pal_idx in zip(fallback_candidates_dmc_idx, nearest_palette.tolist()):
            dmc_to_palette_map[dmc_idx] = pal_idx

    # ------------------------------------------------------------------
    # Step 6: Reconstruct the 2D index grid
    # ------------------------------------------------------------------
    flat_palette_indices = dmc_to_palette_map[flat_dmc_indices]  # (total_pixels,)
    index_grid = flat_palette_indices.reshape(height, width).tolist()

    palette = Palette(colors=[(dmc.r, dmc.g, dmc.b) for dmc in dmc_list])
    return palette, index_grid, dmc_list
