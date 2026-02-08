from typing import List, Tuple

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.application.use_cases.calculate_fabric_requirements import (
    CalculateFabricRequirements,
    FabricRequirementsRequest,
)
from app.application.use_cases.convert_image_to_pattern import (
    ConvertImageRequest,
    ConvertImageToPattern,
)
from app.application.use_cases.export_pattern_to_pdf import (
    ExportPatternToPdf,
    ExportPdfRequest,
)
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Palette, Pattern, PatternGrid
from app.infrastructure.image_processing.pillow_image_resizer import PillowImageResizer

router = APIRouter()


# -----------------------------
# Calculate fabric requirements
# -----------------------------

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
    result = use_case.execute(
        FabricRequirementsRequest(
            pattern_width=body.pattern_width,
            pattern_height=body.pattern_height,
            aida_count=body.aida_count,
            num_colors=body.num_colors,
            margin_cm=body.margin_cm,
            num_strands=body.num_strands,
        )
    )

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


# -----------------------------
# Convert image to pattern
# -----------------------------

class GridInfo(BaseModel):
    width: int
    height: int
    cells: List[List[int]]


class DmcColorInfo(BaseModel):
    number: str
    name: str
    r: int
    g: int
    b: int


class ConvertResponseBody(BaseModel):
    grid: GridInfo
    palette: List[List[int]]
    dmc_colors: List[DmcColorInfo]


def get_convert_use_case() -> ConvertImageToPattern:
    return ConvertImageToPattern(image_resizer=PillowImageResizer())


@router.post("/convert", response_model=ConvertResponseBody)
async def convert_image(
    file: UploadFile,
    target_width: int = Form(gt=0),
    target_height: int = Form(gt=0),
    num_colors: int = Form(gt=0),
    use_case: ConvertImageToPattern = Depends(get_convert_use_case),
) -> ConvertResponseBody:
    image_data = await file.read()

    result = use_case.execute(
        ConvertImageRequest(
            image_data=image_data,
            target_width=target_width,
            target_height=target_height,
            num_colors=num_colors,
        )
    )

    return ConvertResponseBody(
        grid=GridInfo(
            width=result.pattern.grid.width,
            height=result.pattern.grid.height,
            cells=result.pattern.grid.cells,
        ),
        palette=[list(c) for c in result.pattern.palette.colors],
        dmc_colors=[
            DmcColorInfo(
                number=dmc.number,
                name=dmc.name,
                r=dmc.r,
                g=dmc.g,
                b=dmc.b,
            )
            for dmc in result.dmc_colors
        ],
    )


# -----------------------------
# Export pattern to PDF
# -----------------------------

class ExportPdfRequestBody(BaseModel):
    grid: GridInfo
    palette: List[List[int]]
    dmc_colors: List[DmcColorInfo]
    title: str = Field(min_length=1)
    aida_count: int = Field(default=14, gt=0)
    num_strands: int = Field(default=2, ge=1, le=6)
    margin_cm: float = Field(default=5.0, ge=0)
    variant: str = Field(default="color", pattern="^(color|bw)$")


@router.post("/export-pdf")
def export_pdf(body: ExportPdfRequestBody) -> Response:
    palette_tuples: List[Tuple[int, int, int]] = [(c[0], c[1], c[2]) for c in body.palette]

    pattern = Pattern(
        grid=PatternGrid(
            width=body.grid.width,
            height=body.grid.height,
            cells=body.grid.cells,
        ),
        palette=Palette(colors=palette_tuples),
    )

    dmc_colors = [
        DmcColor(number=d.number, name=d.name, r=d.r, g=d.g, b=d.b)
        for d in body.dmc_colors
    ]

    use_case = ExportPatternToPdf()
    result = use_case.execute(
        ExportPdfRequest(
            pattern=pattern,
            dmc_colors=dmc_colors,
            title=body.title,
            aida_count=body.aida_count,
            num_strands=body.num_strands,
            margin_cm=body.margin_cm,
            variant=body.variant,
        )
    )

    return Response(content=result.pdf_bytes, media_type="application/pdf")
