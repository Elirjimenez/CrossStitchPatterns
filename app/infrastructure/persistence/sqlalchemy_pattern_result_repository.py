from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain.model.project import PatternResult
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.infrastructure.persistence.mappers.pattern_result_mapper import PatternResultMapper
from app.infrastructure.persistence.models.pattern_result_model import PatternResultModel


class SqlAlchemyPatternResultRepository(PatternResultRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, pattern_result: PatternResult) -> None:
        model = PatternResultMapper.to_model(pattern_result)
        self._session.add(model)
        self._session.flush()

    def list_by_project(self, project_id: str) -> List[PatternResult]:
        models = (
            self._session.query(PatternResultModel)
            .filter(PatternResultModel.project_id == project_id)
            .order_by(PatternResultModel.created_at.desc())
            .all()
        )
        return [PatternResultMapper.to_domain(m) for m in models]

    def get_latest_by_project(self, project_id: str) -> Optional[PatternResult]:
        model = (
            self._session.query(PatternResultModel)
            .filter(PatternResultModel.project_id == project_id)
            .order_by(PatternResultModel.created_at.desc())
            .first()
        )
        if model is None:
            return None
        return PatternResultMapper.to_domain(model)
