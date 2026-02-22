"""Shared pattern-build workflow: image → pattern → PDF.

Extracted from CreateCompletePattern so it can be reused by
CompleteExistingProject without code duplication.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.application.ports.file_storage import FileStorage
from app.application.ports.image_resizer import ImageResizer
from app.application.ports.pattern_pdf_exporter import LegendEntryDTO, PatternPdfExporter
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Pattern, PatternGrid
from app.domain.model.project import PatternResult
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.services.color_matching import select_palette
from app.domain.services.confetti import reduce_confetti
from app.domain.services.image_mode_detector import DeterministicHeuristicImageModeDetector
from app.domain.services.fabric import compute_fabric_size_cm
from app.domain.services.floss import compute_per_color_floss
from app.domain.services.pattern_tiling import (
    compute_cell_size_mm,
    compute_tiles,
    cols_per_page,
    rows_per_page,
)
from app.domain.services.stitch_count import count_stitches_per_color
from app.domain.services.symbol_map import assign_symbols


_mode_detector = DeterministicHeuristicImageModeDetector()

# Maps image mode to PIL resampling filter name
_RESAMPLING_FOR_MODE = {
    "pixel_art": "nearest",
    "drawing": "bilinear",
    "photo": "lanczos",
}


@dataclass(frozen=True)
class PatternWorkflowRequest:
    """Parameters for the image → pattern → PDF pipeline."""

    image_data: bytes
    num_colors: int
    target_width: int
    target_height: int
    min_frequency_pct: float = 1.0
    aida_count: int = 14
    num_strands: int = 2
    margin_cm: float = 5.0
    variant: str = "color"
    processing_mode: str = "auto"  # "auto" | "photo" | "drawing" | "pixel_art"


@dataclass(frozen=True)
class PatternWorkflowResult:
    """Artifacts produced by the pipeline, before persistence."""

    pattern: Pattern
    dmc_colors: List[DmcColor]
    pdf_bytes: bytes
    legend_entries: List[LegendEntryDTO]


def run_pattern_workflow(
    request: PatternWorkflowRequest,
    image_resizer: ImageResizer,
    pdf_exporter: PatternPdfExporter,
    title: str,
) -> PatternWorkflowResult:
    """Convert image bytes to a cross-stitch pattern and export to PDF.

    Args:
        request: Pipeline parameters (dimensions, colours, fabric settings).
        image_resizer: Port for loading and resizing images.
        pdf_exporter: Port for rendering the PDF.
        title: Pattern title used in the PDF header.

    Returns:
        PatternWorkflowResult containing the Pattern, DMC colours, and PDF bytes.
    """
    # Determine effective processing mode
    mode = request.processing_mode
    if mode == "auto":
        thumbnail = image_resizer.load_and_resize(
            request.image_data, 64, 64, resampling="nearest"
        )
        mode = _mode_detector.detect(thumbnail).mode

    resampling = _RESAMPLING_FOR_MODE.get(mode, "lanczos")
    min_freq = 0.0 if mode == "pixel_art" else request.min_frequency_pct

    pixels = image_resizer.load_and_resize(
        request.image_data, request.target_width, request.target_height,
        resampling=resampling,
    )
    palette, index_grid, dmc_colors = select_palette(
        pixels, request.num_colors, min_freq
    )
    if mode != "pixel_art":
        index_grid = reduce_confetti(index_grid)

    grid = PatternGrid(
        width=request.target_width,
        height=request.target_height,
        cells=index_grid,
    )
    pattern = Pattern(grid=grid, palette=palette)

    fabric_size = compute_fabric_size_cm(
        stitches_w=pattern.grid.width,
        stitches_h=pattern.grid.height,
        aida_count=request.aida_count,
        margin_cm=request.margin_cm,
    )

    stitch_counts = count_stitches_per_color(pattern.grid)
    symbols = assign_symbols(len(pattern.palette.colors))
    floss = compute_per_color_floss(stitch_counts, request.aida_count, request.num_strands)

    legend_entries: List[LegendEntryDTO] = []
    for f in floss:
        dmc = dmc_colors[f.palette_index]
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

    cell_size_mm = compute_cell_size_mm(pattern.grid.width, pattern.grid.height)
    tiling = compute_tiles(
        grid_width=pattern.grid.width,
        grid_height=pattern.grid.height,
        cols_per_page=cols_per_page(cell_size_mm),
        rows_per_page=rows_per_page(cell_size_mm),
    )

    pdf_bytes = pdf_exporter.render(
        pattern=pattern,
        title=title,
        fabric_size=fabric_size,
        aida_count=request.aida_count,
        margin_cm=request.margin_cm,
        legend_entries=legend_entries,
        variant=request.variant,
        symbols=symbols,
        tiles=tiling.tiles,
        cell_size_mm=cell_size_mm,
    )

    return PatternWorkflowResult(
        pattern=pattern,
        dmc_colors=dmc_colors,
        pdf_bytes=pdf_bytes,
        legend_entries=legend_entries,
    )


def serialize_palette(palette, dmc_colors: List[DmcColor]) -> Dict[str, Any]:
    """Serialize palette and DMC colours for PatternResult storage."""
    return {
        "colors": [{"r": c[0], "g": c[1], "b": c[2]} for c in palette.colors],
        "dmc_colors": [
            {"number": d.number, "name": d.name, "r": d.r, "g": d.g, "b": d.b}
            for d in dmc_colors
        ],
    }


def build_and_save_pattern_result(
    project_id: str,
    workflow_result: PatternWorkflowResult,
    pdf_ref: str,
    pattern_result_repo: PatternResultRepository,
    processing_mode: str = "auto",
    variant: str = "color",
) -> PatternResult:
    """Persist a PatternResult from the workflow output and return it."""
    stitch_counts = count_stitches_per_color(workflow_result.pattern.grid)
    total_stitches = sum(sc.count for sc in stitch_counts)

    pattern_result = PatternResult(
        id=str(uuid.uuid4()),
        project_id=project_id,
        created_at=datetime.now(timezone.utc),
        palette=serialize_palette(workflow_result.pattern.palette, workflow_result.dmc_colors),
        grid_width=workflow_result.pattern.grid.width,
        grid_height=workflow_result.pattern.grid.height,
        stitch_count=total_stitches,
        pdf_ref=pdf_ref,
        processing_mode=processing_mode,
        variant=variant,
    )
    pattern_result_repo.add(pattern_result)
    return pattern_result
