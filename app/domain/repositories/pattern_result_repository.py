from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.model.project import PatternResult


class PatternResultRepository(ABC):

    @abstractmethod
    def add(self, pattern_result: PatternResult) -> None:
        pass

    @abstractmethod
    def list_by_project(self, project_id: str) -> List[PatternResult]:
        pass

    @abstractmethod
    def get_latest_by_project(self, project_id: str) -> Optional[PatternResult]:
        pass

    @abstractmethod
    def delete_by_project(self, project_id: str) -> None:
        pass
