from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.ports.file_storage import FileStorage
from app.config import get_settings
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.persistence.database import build_session_factory
from app.infrastructure.persistence.sqlalchemy_pattern_result_repository import (
    SqlAlchemyPatternResultRepository,
)
from app.infrastructure.persistence.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.storage.local_file_storage import LocalFileStorage

_session_factory = None


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        settings = get_settings()
        _session_factory = build_session_factory(settings.database_url)
    return _session_factory


def get_db_session() -> Generator[Session, None, None]:
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_file_storage() -> FileStorage:
    settings = get_settings()
    return LocalFileStorage(settings.storage_dir)


def get_project_repository(
    session: Session = Depends(get_db_session),
) -> ProjectRepository:
    """Dependency for ProjectRepository."""
    return SqlAlchemyProjectRepository(session)


def get_pattern_result_repository(
    session: Session = Depends(get_db_session),
) -> PatternResultRepository:
    """Dependency for PatternResultRepository."""
    return SqlAlchemyPatternResultRepository(session)
