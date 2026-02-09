from __future__ import annotations

from app.domain.exceptions import ProjectNotFoundError
from app.domain.model.project import Project
from app.domain.repositories.project_repository import ProjectRepository


class GetProject:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: str) -> Project:
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project '{project_id}' not found")
        return project
