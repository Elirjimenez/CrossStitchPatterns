from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.model.project import Project, ProjectStatus


class ProjectRepository(ABC):

    @abstractmethod
    def add(self, project: Project) -> None:
        pass

    @abstractmethod
    def get(self, project_id: str) -> Optional[Project]:
        pass

    @abstractmethod
    def list_all(self) -> List[Project]:
        pass

    @abstractmethod
    def update_status(self, project_id: str, status: ProjectStatus) -> None:
        pass
