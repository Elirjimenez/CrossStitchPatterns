from __future__ import annotations
from dataclasses import dataclass
from math import ceil
from typing import List

from app.domain.exceptions import InvalidFabricParametersError
from app.domain.services.stitch_count import ColorStitchCount

SKEIN_LENGTH_M = 8.0
STRANDS_PER_SKEIN = 6
THREAD_CONSTANT_CM = 19.6  # thread_per_stitch = THREAD_CONSTANT_CM / aida_count


@dataclass(frozen=True)
class FlossEstimate:
    total_stitches: int
    num_colors: int
    skeins_per_color: int
    total_skeins: int


def compute_floss_estimate(
    total_stitches: int,
    num_colors: int,
    aida_count: int,
    num_strands: int = 2,
    margin_ratio: float = 0.2,
) -> FlossEstimate:
    """
    Estimate floss/thread requirements for a cross-stitch pattern.

    Args:
        total_stitches: Total number of stitches in the pattern.
        num_colors: Number of distinct thread colors.
        aida_count: Fabric count (stitches per inch, e.g. 14, 16, 18).
        num_strands: Number of strands used per stitch (1-6, default 2).
        margin_ratio: Safety margin ratio (default 0.2 = 20%).
    """
    if total_stitches <= 0:
        raise InvalidFabricParametersError("total_stitches must be > 0")
    if num_colors <= 0:
        raise InvalidFabricParametersError("num_colors must be > 0")
    if aida_count <= 0:
        raise InvalidFabricParametersError("aida_count must be > 0")
    if not 1 <= num_strands <= 6:
        raise InvalidFabricParametersError("num_strands must be between 1 and 6")
    if margin_ratio < 0:
        raise InvalidFabricParametersError("margin_ratio must be >= 0")

    thread_per_stitch_cm = THREAD_CONSTANT_CM / aida_count
    single_strand_per_skein_cm = SKEIN_LENGTH_M * 100 * STRANDS_PER_SKEIN / num_strands
    stitches_per_skein = single_strand_per_skein_cm / thread_per_stitch_cm

    stitches_per_color = total_stitches / num_colors
    stitches_with_margin = stitches_per_color * (1 + margin_ratio)
    skeins_per_color = ceil(stitches_with_margin / stitches_per_skein)
    total_skeins = skeins_per_color * num_colors

    return FlossEstimate(
        total_stitches=total_stitches,
        num_colors=num_colors,
        skeins_per_color=skeins_per_color,
        total_skeins=total_skeins,
    )


@dataclass(frozen=True)
class ColorFlossEstimate:
    palette_index: int
    stitch_count: int
    skeins: int


def compute_per_color_floss(
    color_stitch_counts: List[ColorStitchCount],
    aida_count: int,
    num_strands: int = 2,
    margin_ratio: float = 0.2,
) -> List[ColorFlossEstimate]:
    if aida_count <= 0:
        raise InvalidFabricParametersError("aida_count must be > 0")
    if not 1 <= num_strands <= 6:
        raise InvalidFabricParametersError("num_strands must be between 1 and 6")
    if margin_ratio < 0:
        raise InvalidFabricParametersError("margin_ratio must be >= 0")

    thread_per_stitch_cm = THREAD_CONSTANT_CM / aida_count
    single_strand_per_skein_cm = SKEIN_LENGTH_M * 100 * STRANDS_PER_SKEIN / num_strands
    stitches_per_skein = single_strand_per_skein_cm / thread_per_stitch_cm

    results = []
    for csc in sorted(color_stitch_counts, key=lambda c: c.palette_index):
        stitches_with_margin = csc.count * (1 + margin_ratio)
        skeins = ceil(stitches_with_margin / stitches_per_skein)
        results.append(
            ColorFlossEstimate(
                palette_index=csc.palette_index,
                stitch_count=csc.count,
                skeins=skeins,
            )
        )

    return results
