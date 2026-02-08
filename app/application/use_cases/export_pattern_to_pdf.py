from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.application.ports.pattern_pdf_exporter import LegendEntryDTO, PatternPdfExporter
from app.domain.data.dmc_colors import DmcColor
from app.domain.exceptions import DomainException
from app.domain.model.pattern import Pattern
from app.domain.services.fabric import compute_fabric_size_cm
from app.domain.services.floss import compute_per_color_floss
from app.domain.services.stitch_count import count_stitches_per_color
from app.domain.services.symbol_map import assign_symbols

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
    def __init__(self, exporter: PatternPdfExporter):
        self._exporter = exporter

    def execute(self, request: ExportPdfRequest) -> ExportPdfResult:
        if not request.title.strip():
            raise DomainException("title must not be empty")
        if request.variant not in VALID_VARIANTS:
            raise DomainException(
                f"variant must be one of {VALID_VARIANTS}, got '{request.variant}'"
            )

        if len(request.dmc_colors) != len(request.pattern.palette.colors):
            raise DomainException(
                "dmc_colors length must match pattern palette length"
            )

        fabric_size = compute_fabric_size_cm(
            stitches_w=request.pattern.grid.width,
            stitches_h=request.pattern.grid.height,
            aida_count=request.aida_count,
            margin_cm=request.margin_cm,
        )

        stitch_counts = count_stitches_per_color(request.pattern.grid)
        symbols = assign_symbols(len(request.pattern.palette.colors))
        floss = compute_per_color_floss(stitch_counts, request.aida_count, request.num_strands)

        legend_entries: List[LegendEntryDTO] = []
        for f in floss:
            dmc = request.dmc_colors[f.palette_index]
            sym = symbols[f.palette_index]
            legend_entries.append(
                LegendEntryDTO(
                    symbol=sym,
                    dmc_number=dmc.number,
                    dmc_name=dmc.name,
                    r=dmc.r,
                    g=dmc.g,
                    b=dmc.b,
                    stitch_count=f.stitch_count,
                    skeins=f.skeins,
                )
            )

        pdf_bytes = self._exporter.render(
            pattern=request.pattern,
            title=request.title,
            fabric_size=fabric_size,
            aida_count=request.aida_count,
            margin_cm=request.margin_cm,
            legend_entries=legend_entries,
            variant=request.variant,
        )

        # If your exporter doesn't report num_pages yet, keep it stable:
        # either set to 1 or leave as 2 if that's your current PDF structure.
        return ExportPdfResult(
            pdf_bytes=pdf_bytes,
            num_pages=2,
            variant=request.variant,
        )
