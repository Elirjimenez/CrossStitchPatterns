from abc import ABC, abstractmethod
from app.domain.model.pattern import Pattern


class PatternRepository(ABC):

    @abstractmethod
    def save(self, pattern: Pattern) -> str:
        """Save pattern and return ID"""
        pass

    @abstractmethod
    def find_by_id(self, pattern_id: str) -> Pattern:

        pass
