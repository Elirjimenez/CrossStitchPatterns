from __future__ import annotations

from typing import List

from app.domain.model.project import Project
from app.domain.repositories.project_repository import ProjectRepository


class ListProjects:
    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self) -> List[Project]:
        return self._project_repo.list_all()
