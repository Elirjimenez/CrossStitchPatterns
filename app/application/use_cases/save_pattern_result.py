from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.domain.exceptions import ProjectNotFoundError
from app.domain.model.project import PatternResult
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository


@dataclass(frozen=True)
class SavePatternResultRequest:
    project_id: str
    palette: Dict[str, Any]
    grid_width: int
    grid_height: int
    stitch_count: int
    pdf_ref: Optional[str] = None


class SavePatternResult:
    def __init__(
        self,
        project_repo: ProjectRepository,
        pattern_result_repo: PatternResultRepository,
    ) -> None:
        self._project_repo = project_repo
        self._pattern_result_repo = pattern_result_repo

    def execute(self, request: SavePatternResultRequest) -> PatternResult:
        project = self._project_repo.get(request.project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project '{request.project_id}' not found")

        pattern_result = PatternResult(
            id=str(uuid.uuid4()),
            project_id=request.project_id,
            created_at=datetime.now(timezone.utc),
            palette=request.palette,
            grid_width=request.grid_width,
            grid_height=request.grid_height,
            stitch_count=request.stitch_count,
            pdf_ref=request.pdf_ref,
        )
        self._pattern_result_repo.add(pattern_result)
        return pattern_result
