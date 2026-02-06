from __future__ import annotations
from dataclasses import dataclass

from app.domain.services.fabric import compute_fabric_size_cm
from app.domain.services.floss import compute_floss_estimate


@dataclass(frozen=True)
class FabricRequirementsRequest:
    pattern_width: int
    pattern_height: int
    aida_count: int
    num_colors: int
    margin_cm: float = 5.0
    num_strands: int = 2
    margin_ratio: float = 0.2


@dataclass(frozen=True)
class FabricRequirementsResult:
    fabric_width_cm: float
    fabric_height_cm: float
    total_stitches: int
    num_colors: int
    skeins_per_color: int
    total_skeins: int


class CalculateFabricRequirements:
    def execute(self, request: FabricRequirementsRequest) -> FabricRequirementsResult:
        fabric = compute_fabric_size_cm(
            stitches_w=request.pattern_width,
            stitches_h=request.pattern_height,
            aida_count=request.aida_count,
            margin_cm=request.margin_cm,
        )

        total_stitches = request.pattern_width * request.pattern_height

        floss = compute_floss_estimate(
            total_stitches=total_stitches,
            num_colors=request.num_colors,
            aida_count=request.aida_count,
            num_strands=request.num_strands,
            margin_ratio=request.margin_ratio,
        )

        return FabricRequirementsResult(
            fabric_width_cm=fabric.width_cm,
            fabric_height_cm=fabric.height_cm,
            total_stitches=floss.total_stitches,
            num_colors=floss.num_colors,
            skeins_per_color=floss.skeins_per_color,
            total_skeins=floss.total_skeins,
        )
