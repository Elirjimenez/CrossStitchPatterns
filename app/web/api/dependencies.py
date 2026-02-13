from typing import Generator

from sqlalchemy.orm import Session

from app.application.ports.file_storage import FileStorage
from app.config import get_settings
from app.infrastructure.persistence.database import build_session_factory
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
