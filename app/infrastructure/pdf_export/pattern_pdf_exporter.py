from __future__ import annotations

from typing import List, Optional

from app.application.ports.pattern_pdf_exporter import (
    LegendEntryDTO,
    PatternPdfExporter,
)
from app.domain.model.pattern import Pattern
from app.domain.services.fabric import FabricSize
from app.domain.services.pattern_tiling import PageTile
from app.infrastructure.pdf_export.pdf_generator import (
    LegendEntry,
    render_pattern_pdf,
)


class ReportLabPatternPdfExporter(PatternPdfExporter):
    def render(
        self,
        pattern: Pattern,
        title: str,
        fabric_size: FabricSize,
        aida_count: int,
        margin_cm: float,
        legend_entries: List[LegendEntryDTO],
        variant: str = "color",
        symbols: Optional[List[str]] = None,
        tiles: Optional[List[PageTile]] = None,
    ) -> bytes:
        infra_legend_entries = [
            LegendEntry(
                symbol=e.symbol,
                dmc_number=e.dmc_number,
                dmc_name=e.dmc_name,
                r=e.r,
                g=e.g,
                b=e.b,
                stitch_count=e.stitch_count,
                skeins=e.skeins,
            )
            for e in legend_entries
        ]

        return render_pattern_pdf(
            pattern=pattern,
            title=title,
            fabric_size=fabric_size,
            aida_count=aida_count,
            margin_cm=margin_cm,
            legend_entries=infra_legend_entries,
            symbols=symbols,
            tiles=tiles,
            variant=variant,
        )
