from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.application.use_cases.calculate_fabric_requirements import (
    CalculateFabricRequirements,
    FabricRequirementsRequest,
)

router = APIRouter()


class FabricRequestBody(BaseModel):
    pattern_width: int = Field(gt=0)
    pattern_height: int = Field(gt=0)
    aida_count: int = Field(gt=0)
    num_colors: int = Field(gt=0)
    margin_cm: float = Field(default=5.0, ge=0)
    num_strands: int = Field(default=2, ge=1, le=6)


class FabricInfo(BaseModel):
    width_cm: float
    height_cm: float


class ThreadInfo(BaseModel):
    total_stitches: int
    num_colors: int
    skeins_per_color: int
    total_skeins: int


class FabricResponseBody(BaseModel):
    fabric: FabricInfo
    thread: ThreadInfo


@router.post("/calculate-fabric", response_model=FabricResponseBody)
def calculate_fabric(body: FabricRequestBody) -> FabricResponseBody:
    use_case = CalculateFabricRequirements()
    result = use_case.execute(FabricRequirementsRequest(
        pattern_width=body.pattern_width,
        pattern_height=body.pattern_height,
        aida_count=body.aida_count,
        num_colors=body.num_colors,
        margin_cm=body.margin_cm,
        num_strands=body.num_strands,
    ))

    return FabricResponseBody(
        fabric=FabricInfo(
            width_cm=result.fabric_width_cm,
            height_cm=result.fabric_height_cm,
        ),
        thread=ThreadInfo(
            total_stitches=result.total_stitches,
            num_colors=result.num_colors,
            skeins_per_color=result.skeins_per_color,
            total_skeins=result.total_skeins,
        ),
    )
