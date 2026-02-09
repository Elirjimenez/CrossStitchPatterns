from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.domain.model.project import Project, ProjectStatus
from app.domain.repositories.project_repository import ProjectRepository


@dataclass(frozen=True)
class CreateProjectRequest:
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    source_image_ref: Optional[str] = None


class CreateProject:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, request: CreateProjectRequest) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            name=request.name,
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=request.source_image_ref,
            parameters=request.parameters,
        )
        self._project_repo.add(project)
        return project
