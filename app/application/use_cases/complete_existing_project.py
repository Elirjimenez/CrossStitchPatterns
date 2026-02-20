"""Use case: generate a pattern + PDF for an already-created project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.application.ports.file_storage import FileStorage
from app.application.ports.image_resizer import ImageResizer
from app.application.ports.pattern_pdf_exporter import PatternPdfExporter
from app.application.services.pattern_workflow import (
    PatternWorkflowRequest,
    PatternWorkflowResult,
    build_and_save_pattern_result,
    run_pattern_workflow,
)
from app.domain.data.dmc_colors import DmcColor
from app.domain.exceptions import DomainException, ProjectNotFoundError
from app.domain.model.pattern import Pattern
from app.domain.model.project import PatternResult, Project, ProjectStatus
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository


@dataclass(frozen=True)
class CompleteExistingProjectRequest:
    """Request to generate a pattern for a project that already has a source image.

    The project must exist and have a source_image_ref set. The image is read
    from file storage; no re-upload is required.
    """

    project_id: str
    num_colors: int
    target_width: int
    target_height: int
    min_frequency_pct: float = 1.0
    aida_count: int = 14
    num_strands: int = 2
    margin_cm: float = 5.0
    variant: str = "color"


@dataclass(frozen=True)
class CompleteExistingProjectResult:
    """All artifacts produced by the pattern-generation pipeline."""

    project: Project
    pattern: Pattern
    dmc_colors: List[DmcColor]
    pattern_result: PatternResult
    pdf_bytes: bytes


class CompleteExistingProject:
    """Generate a cross-stitch pattern and PDF for an existing project.

    Workflow:
    1. Fetch project — raise ProjectNotFoundError if missing.
    2. Assert source image is present — raise DomainException if not.
    3. Read image bytes from storage.
    4. Set project status to IN_PROGRESS.
    5. Run image → pattern → PDF pipeline.
    6. Save PDF and PatternResult; set status to COMPLETED.
    7. On any processing failure, set status to FAILED and re-raise.
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

    def execute(self, request: CompleteExistingProjectRequest) -> CompleteExistingProjectResult:
        """Execute the pattern-generation workflow for the given project."""
        project_id = request.project_id

        # 1. Fetch project
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)

        # 2. Assert source image present
        if not project.source_image_ref:
            raise DomainException(
                f"Project '{project_id}' has no source image. Upload an image first."
            )

        # 3. Read image bytes
        image_data = self._file_storage.read_source_image(
            project_id, project.source_image_ref
        )

        # 4. Mark IN_PROGRESS
        self._project_repo.update_status(project_id, ProjectStatus.IN_PROGRESS)

        try:
            # 5. Build pattern + PDF
            workflow_result = run_pattern_workflow(
                request=PatternWorkflowRequest(
                    image_data=image_data,
                    num_colors=request.num_colors,
                    target_width=request.target_width,
                    target_height=request.target_height,
                    min_frequency_pct=request.min_frequency_pct,
                    aida_count=request.aida_count,
                    num_strands=request.num_strands,
                    margin_cm=request.margin_cm,
                    variant=request.variant,
                ),
                image_resizer=self._image_resizer,
                pdf_exporter=self._pdf_exporter,
                title=project.name,
            )

            # 6a. Save PDF
            pdf_ref = self._file_storage.save_pdf(
                project_id=project_id,
                data=workflow_result.pdf_bytes,
                filename="pattern.pdf",
            )

            # 6b. Save PatternResult
            pattern_result = build_and_save_pattern_result(
                project_id=project_id,
                workflow_result=workflow_result,
                pdf_ref=pdf_ref,
                pattern_result_repo=self._pattern_result_repo,
            )

            # 6c. Mark COMPLETED
            self._project_repo.update_status(project_id, ProjectStatus.COMPLETED)

        except Exception:
            self._project_repo.update_status(project_id, ProjectStatus.FAILED)
            raise

        from datetime import datetime, timezone

        completed_project = Project(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            status=ProjectStatus.COMPLETED,
            source_image_ref=project.source_image_ref,
            parameters=project.parameters,
        )

        return CompleteExistingProjectResult(
            project=completed_project,
            pattern=workflow_result.pattern,
            dmc_colors=workflow_result.dmc_colors,
            pattern_result=pattern_result,
            pdf_bytes=workflow_result.pdf_bytes,
        )
