from __future__ import annotations

from typing import Optional

from app.domain.model.project import PatternResult
from app.domain.repositories.pattern_result_repository import PatternResultRepository


class GetLatestPatternByProject:
    def __init__(self, pattern_result_repo: PatternResultRepository) -> None:
        self._pattern_result_repo = pattern_result_repo

    def execute(self, project_id: str) -> Optional[PatternResult]:
        return self._pattern_result_repo.get_latest_by_project(project_id)
