from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.domain.data.dmc_colors import DmcColor
from app.domain.exceptions import DomainException
from app.domain.model.pattern import Pattern
from app.domain.services.fabric import compute_fabric_size_cm
from app.infrastructure.pdf_export.pdf_generator import render_overview_page

VALID_VARIANTS = {"color", "bw"}


@dataclass(frozen=True)
class ExportPdfRequest:
    pattern: Pattern
    dmc_colors: List[DmcColor]
    title: str
    aida_count: int = 14
    num_strands: int = 2
    margin_cm: float = 5.0
    variant: str = "color"


@dataclass(frozen=True)
class ExportPdfResult:
    pdf_bytes: bytes
    num_pages: int
    variant: str


class ExportPatternToPdf:
    def execute(self, request: ExportPdfRequest) -> ExportPdfResult:
        if not request.title.strip():
            raise DomainException("title must not be empty")
        if request.variant not in VALID_VARIANTS:
            raise DomainException(
                f"variant must be one of {VALID_VARIANTS}, got '{request.variant}'"
            )

        fabric_size = compute_fabric_size_cm(
            stitches_w=request.pattern.grid.width,
            stitches_h=request.pattern.grid.height,
            aida_count=request.aida_count,
            margin_cm=request.margin_cm,
        )

        pdf_bytes = render_overview_page(
            pattern=request.pattern,
            title=request.title,
            fabric_size=fabric_size,
            aida_count=request.aida_count,
            margin_cm=request.margin_cm,
        )

        return ExportPdfResult(
            pdf_bytes=pdf_bytes,
            num_pages=1,
            variant=request.variant,
        )
