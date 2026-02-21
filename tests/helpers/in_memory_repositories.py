from typing import Dict, List, Optional

from app.domain.model.project import Project, PatternResult, ProjectStatus
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.pattern_result_repository import PatternResultRepository


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._store: Dict[str, Project] = {}

    def add(self, project: Project) -> None:
        self._store[project.id] = project

    def get(self, project_id: str) -> Optional[Project]:
        return self._store.get(project_id)

    def list_all(self) -> List[Project]:
        return list(self._store.values())

    def update_status(self, project_id: str, status: ProjectStatus) -> None:
        existing = self._store.get(project_id)
        if existing is None:
            return
        # Frozen dataclass: rebuild with new status
        updated = Project(
            id=existing.id,
            name=existing.name,
            created_at=existing.created_at,
            status=status,
            source_image_ref=existing.source_image_ref,
            parameters=existing.parameters,
            source_image_width=existing.source_image_width,
            source_image_height=existing.source_image_height,
        )
        self._store[project_id] = updated

    def update_source_image_ref(self, project_id: str, ref: str) -> None:
        existing = self._store.get(project_id)
        if existing is None:
            return
        updated = Project(
            id=existing.id,
            name=existing.name,
            created_at=existing.created_at,
            status=existing.status,
            source_image_ref=ref,
            parameters=existing.parameters,
            source_image_width=existing.source_image_width,
            source_image_height=existing.source_image_height,
        )
        self._store[project_id] = updated

    def update_source_image_metadata(
        self, project_id: str, *, ref: str, width: int, height: int
    ) -> None:
        existing = self._store.get(project_id)
        if existing is None:
            return
        updated = Project(
            id=existing.id,
            name=existing.name,
            created_at=existing.created_at,
            status=existing.status,
            source_image_ref=ref,
            parameters=existing.parameters,
            source_image_width=width,
            source_image_height=height,
        )
        self._store[project_id] = updated


class InMemoryPatternResultRepository(PatternResultRepository):
    def __init__(self) -> None:
        self._store: List[PatternResult] = []

    def add(self, pattern_result: PatternResult) -> None:
        self._store.append(pattern_result)

    def list_by_project(self, project_id: str) -> List[PatternResult]:
        return [pr for pr in self._store if pr.project_id == project_id]

    def get_latest_by_project(self, project_id: str) -> Optional[PatternResult]:
        matches = [pr for pr in self._store if pr.project_id == project_id]
        if not matches:
            return None
        return max(matches, key=lambda pr: pr.created_at)
