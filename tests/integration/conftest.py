import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.persistence.sqlalchemy_pattern_result_repository import (
    SqlAlchemyPatternResultRepository,
)

POSTGRES_URL = "postgresql://user:pass@localhost:5432/crossstitch"


def _postgres_is_available() -> bool:
    try:
        engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


_PG_AVAILABLE = _postgres_is_available()


@pytest.fixture(scope="session")
def pg_engine():
    if not _PG_AVAILABLE:
        pytest.skip("PostgreSQL is not available")
    engine = create_engine(POSTGRES_URL)
    yield engine
    engine.dispose()


@pytest.fixture()
def pg_session(pg_engine):
    Base.metadata.drop_all(pg_engine)
    Base.metadata.create_all(pg_engine)
    factory = sessionmaker(bind=pg_engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(pg_engine)


@pytest.fixture()
def pg_project_repo(pg_session):
    return SqlAlchemyProjectRepository(pg_session)


@pytest.fixture()
def pg_pattern_repo(pg_session):
    return SqlAlchemyPatternResultRepository(pg_session)
