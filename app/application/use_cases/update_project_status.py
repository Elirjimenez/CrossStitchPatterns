from __future__ import annotations

from app.domain.exceptions import ProjectNotFoundError
from app.domain.model.project import ProjectStatus
from app.domain.repositories.project_repository import ProjectRepository


class UpdateProjectStatus:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: str, status: ProjectStatus) -> None:
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project '{project_id}' not found")
        self._project_repo.update_status(project_id, status)
