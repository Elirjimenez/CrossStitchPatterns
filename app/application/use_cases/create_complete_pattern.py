"""Orchestrating use case that creates a complete pattern from start to finish."""

from __future__ import annotations

import io
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from PIL import Image

from app.application.ports.file_storage import FileStorage
from app.application.ports.image_resizer import ImageResizer
from app.application.ports.pattern_pdf_exporter import PatternPdfExporter
from app.application.services.pattern_workflow import (
    PatternWorkflowRequest,
    build_and_save_pattern_result,
    run_pattern_workflow,
)
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Pattern
from app.domain.model.project import PatternResult, Project, ProjectStatus
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository


@dataclass(frozen=True)
class CreateCompletePatternRequest:
    """Request to create a complete pattern from source image.

    If target_width and target_height are None, the actual image dimensions
    will be used (no resizing).
    """

    name: str
    image_data: bytes
    image_filename: str
    num_colors: int
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    min_frequency_pct: float = 1.0
    aida_count: int = 14
    num_strands: int = 2
    margin_cm: float = 5.0
    variant: str = "color"           # "color" or "bw"
    processing_mode: str = "auto"   # "auto" | "photo" | "drawing" | "pixel_art"


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

        # Determine target dimensions (use image size if not specified)
        target_width = request.target_width
        target_height = request.target_height

        if target_width is None or target_height is None:
            image = Image.open(io.BytesIO(request.image_data))
            if target_width is None:
                target_width = image.width
            if target_height is None:
                target_height = image.height

        # Step 1: Create project
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name=request.name,
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={
                "target_width": target_width,
                "target_height": target_height,
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

        # Steps 4–6: image → pattern → PDF (shared service)
        workflow_result = run_pattern_workflow(
            request=PatternWorkflowRequest(
                image_data=request.image_data,
                num_colors=request.num_colors,
                target_width=target_width,
                target_height=target_height,
                min_frequency_pct=request.min_frequency_pct,
                aida_count=request.aida_count,
                num_strands=request.num_strands,
                margin_cm=request.margin_cm,
                variant=request.variant,
                processing_mode=request.processing_mode,
            ),
            image_resizer=self._image_resizer,
            pdf_exporter=self._pdf_exporter,
            title=request.name,
        )

        # Step 7: Save PDF
        pdf_ref = self._file_storage.save_pdf(
            project_id=project_id,
            data=workflow_result.pdf_bytes,
            filename="pattern.pdf",
        )

        # Step 8: Save PatternResult
        pattern_result = build_and_save_pattern_result(
            project_id=project_id,
            workflow_result=workflow_result,
            pdf_ref=pdf_ref,
            pattern_result_repo=self._pattern_result_repo,
            processing_mode=request.processing_mode,
            variant=request.variant,
        )

        # Step 9: Update project status to COMPLETED
        self._project_repo.update_status(project_id, ProjectStatus.COMPLETED)

        return CreateCompletePatternResult(
            project=Project(
                id=project_id,
                name=project.name,
                created_at=project.created_at,
                status=ProjectStatus.COMPLETED,
                source_image_ref=source_image_ref,
                parameters=project.parameters,
            ),
            pattern=workflow_result.pattern,
            dmc_colors=workflow_result.dmc_colors,
            pattern_result=pattern_result,
            pdf_bytes=workflow_result.pdf_bytes,
        )
