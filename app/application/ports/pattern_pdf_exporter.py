from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol

from app.domain.model.pattern import Pattern
from app.domain.services.fabric import FabricSize
from app.domain.services.pattern_tiling import PageTile


@dataclass(frozen=True)
class LegendEntryDTO:
    symbol: str
    dmc_number: str
    dmc_name: str
    r: int
    g: int
    b: int
    stitch_count: int
    skeins: int


class PatternPdfExporter(Protocol):
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
    ) -> bytes: ...
