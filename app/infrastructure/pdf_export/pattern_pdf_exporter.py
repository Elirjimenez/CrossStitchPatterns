from __future__ import annotations

from typing import List

from app.application.ports.pattern_pdf_exporter import (
    LegendEntryDTO,
    PatternPdfExporter,
)
from app.domain.model.pattern import Pattern
from app.domain.services.fabric import FabricSize
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
    ) -> bytes:
        # Adapt DTO -> infrastructure LegendEntry (renderer-specific)
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

        # If your current renderer doesn't use variant yet, we still accept it
        # to keep the port stable for future extensions.
        return render_pattern_pdf(
            pattern=pattern,
            title=title,
            fabric_size=fabric_size,
            aida_count=aida_count,
            margin_cm=margin_cm,
            legend_entries=infra_legend_entries,
        )
