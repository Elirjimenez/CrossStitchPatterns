"""Orchestrating use case that creates a complete pattern from start to finish."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.application.ports.file_storage import FileStorage
from app.application.ports.image_resizer import ImageResizer
from app.application.ports.pattern_pdf_exporter import (
    LegendEntryDTO,
    PatternPdfExporter,
)
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Pattern
from app.domain.model.project import PatternResult, Project, ProjectStatus
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.services.color_matching import select_palette
from app.domain.services.fabric import compute_fabric_size_cm
from app.domain.services.floss import compute_per_color_floss
from app.domain.services.pattern_tiling import compute_tiles
from app.domain.services.stitch_count import count_stitches_per_color
from app.domain.services.symbol_map import assign_symbols

COLS_PER_PAGE = 32
ROWS_PER_PAGE = 49


@dataclass(frozen=True)
class CreateCompletePatternRequest:
    """Request to create a complete pattern from source image."""

    name: str
    image_data: bytes
    image_filename: str
    target_width: int
    target_height: int
    num_colors: int
    aida_count: int = 14
    num_strands: int = 2
    margin_cm: float = 5.0


@dataclass(frozen=True)
class CreateCompletePatternResult:
    """Result containing all created artifacts."""

    project: Project
    pattern: Pattern
    dmc_colors: List[DmcColor]
    pattern_result: PatternResult
    pdf_bytes: bytes


class CreateCompletePattern:
    """
    Orchestrating use case that creates a complete cross-stitch pattern.

    This use case coordinates the entire workflow:
    1. Create project
    2. Save source image
    3. Convert image to pattern
    4. Export pattern to PDF
    5. Save PDF
    6. Save pattern result
    7. Update project status to COMPLETED

    All operations are performed within a single transaction context.
    If any step fails, the entire operation should be rolled back.
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        pattern_result_repo: PatternResultRepository,
        file_storage: FileStorage,
        image_resizer: ImageResizer,
        pdf_exporter: PatternPdfExporter,
    ) -> None:
        self._project_repo = project_repo
        self._pattern_result_repo = pattern_result_repo
        self._file_storage = file_storage
        self._image_resizer = image_resizer
        self._pdf_exporter = pdf_exporter

    def execute(self, request: CreateCompletePatternRequest) -> CreateCompletePatternResult:
        """Execute the complete pattern creation workflow."""

        # Step 1: Create project
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name=request.name,
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={
                "target_width": request.target_width,
                "target_height": request.target_height,
                "num_colors": request.num_colors,
                "aida_count": request.aida_count,
                "num_strands": request.num_strands,
                "margin_cm": request.margin_cm,
            },
        )
        self._project_repo.add(project)

        # Step 2: Save source image
        _, extension = os.path.splitext(request.image_filename)
        source_image_ref = self._file_storage.save_source_image(
            project_id=project_id,
            data=request.image_data,
            extension=extension,
        )
        self._project_repo.update_source_image_ref(project_id, source_image_ref)

        # Step 3: Update project status to IN_PROGRESS
        self._project_repo.update_status(project_id, ProjectStatus.IN_PROGRESS)

        # Step 4: Convert image to pattern
        pixels = self._image_resizer.load_and_resize(
            request.image_data, request.target_width, request.target_height
        )
        palette, index_grid, dmc_colors = select_palette(pixels, request.num_colors)

        from app.domain.model.pattern import PatternGrid

        grid = PatternGrid(
            width=request.target_width,
            height=request.target_height,
            cells=index_grid,
        )
        pattern = Pattern(grid=grid, palette=palette)

        # Step 5: Export pattern to PDF
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

        tiling = compute_tiles(
            grid_width=pattern.grid.width,
            grid_height=pattern.grid.height,
            cols_per_page=COLS_PER_PAGE,
            rows_per_page=ROWS_PER_PAGE,
        )

        pdf_bytes = self._pdf_exporter.render(
            pattern=pattern,
            title=request.name,
            fabric_size=fabric_size,
            aida_count=request.aida_count,
            margin_cm=request.margin_cm,
            legend_entries=legend_entries,
            variant="color",
            symbols=symbols,
            tiles=tiling.tiles,
        )

        # Step 6: Save PDF
        pdf_ref = self._file_storage.save_pdf(
            project_id=project_id,
            data=pdf_bytes,
            filename="pattern.pdf",
        )

        # Step 7: Save pattern result
        total_stitches = sum(sc.count for sc in stitch_counts)
        pattern_result = PatternResult(
            id=str(uuid.uuid4()),
            project_id=project_id,
            created_at=datetime.now(timezone.utc),
            palette=self._serialize_palette(palette, dmc_colors),
            grid_width=pattern.grid.width,
            grid_height=pattern.grid.height,
            stitch_count=total_stitches,
            pdf_ref=pdf_ref,
        )
        self._pattern_result_repo.add(pattern_result)

        # Step 8: Update project status to COMPLETED
        self._project_repo.update_status(project_id, ProjectStatus.COMPLETED)

        # Step 9: Return all artifacts
        return CreateCompletePatternResult(
            project=Project(
                id=project_id,
                name=project.name,
                created_at=project.created_at,
                status=ProjectStatus.COMPLETED,
                source_image_ref=source_image_ref,
                parameters=project.parameters,
            ),
            pattern=pattern,
            dmc_colors=dmc_colors,
            pattern_result=pattern_result,
            pdf_bytes=pdf_bytes,
        )

    def _serialize_palette(self, palette, dmc_colors: List[DmcColor]) -> Dict[str, Any]:
        """Serialize palette and DMC colors for storage."""
        return {
            "colors": [{"r": color[0], "g": color[1], "b": color[2]} for color in palette.colors],
            "dmc_colors": [
                {
                    "number": dmc.number,
                    "name": dmc.name,
                    "r": dmc.r,
                    "g": dmc.g,
                    "b": dmc.b,
                }
                for dmc in dmc_colors
            ],
        }
