from __future__ import annotations
from dataclasses import dataclass
from math import ceil

from app.domain.exceptions import InvalidFabricParametersError


@dataclass(frozen=True)
class FabricSize:
    width_cm: float
    height_cm: float


def compute_fabric_size_cm(
    stitches_w: int, stitches_h: int, aida_count: int, margin_cm: float = 5.0
) -> FabricSize:
    """
    aida_count = stitches per inch (e.g., 14ct, 16ct, 18ct).
    Convert stitches to cm and add margin on each side (total +2*margin).
    """
    if stitches_w <= 0 or stitches_h <= 0:
        raise InvalidFabricParametersError("stitches must be > 0")
    if aida_count <= 0:
        raise InvalidFabricParametersError("aida_count must be > 0")
    if margin_cm < 0:
        raise InvalidFabricParametersError("margin_cm must be >= 0")

    inches_w = stitches_w / aida_count
    inches_h = stitches_h / aida_count
    cm_per_inch = 2.54

    width_cm = inches_w * cm_per_inch + 2 * margin_cm
    height_cm = inches_h * cm_per_inch + 2 * margin_cm
    return FabricSize(width_cm=width_cm, height_cm=height_cm)
