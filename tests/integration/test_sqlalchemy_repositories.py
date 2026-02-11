import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.domain.model.project import Project, PatternResult, ProjectStatus
from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.persistence.sqlalchemy_pattern_result_repository import (
    SqlAlchemyPatternResultRepository,
)


def _enable_sqlite_fk(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", _enable_sqlite_fk)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def project_repo(db_session):
    return SqlAlchemyProjectRepository(db_session)


@pytest.fixture
def pattern_repo(db_session):
    return SqlAlchemyPatternResultRepository(db_session)


def _make_project(
    project_id: str = "proj-1",
    name: str = "Test",
    status: ProjectStatus = ProjectStatus.CREATED,
) -> Project:
    return Project(
        id=project_id,
        name=name,
        created_at=datetime.now(timezone.utc),
        status=status,
        source_image_ref=None,
        parameters={"num_colors": 8},
    )


# --- ProjectRepository CRUD ---


class TestProjectRepositoryCrud:
    def test_add_and_get(self, project_repo, db_session):
        project = _make_project("proj-1", "Landscape")
        project_repo.add(project)
        db_session.commit()

        result = project_repo.get("proj-1")
        assert result is not None
        assert result.id == "proj-1"
        assert result.name == "Landscape"

    def test_get_returns_none_for_missing(self, project_repo):
        result = project_repo.get("nonexistent")
        assert result is None

    def test_list_all_empty(self, project_repo):
        result = project_repo.list_all()
        assert result == []

    def test_list_all_returns_projects(self, project_repo, db_session):
        project_repo.add(_make_project("proj-1", "First"))
        project_repo.add(_make_project("proj-2", "Second"))
        db_session.commit()

        result = project_repo.list_all()
        assert len(result) == 2

    def test_update_status(self, project_repo, db_session):
        project_repo.add(_make_project("proj-1"))
        db_session.commit()

        project_repo.update_status("proj-1", ProjectStatus.COMPLETED)
        db_session.commit()

        result = project_repo.get("proj-1")
        assert result.status == ProjectStatus.COMPLETED

    def test_update_status_preserves_other_fields(self, project_repo, db_session):
        project_repo.add(
            Project(
                id="proj-1",
                name="Original",
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                status=ProjectStatus.CREATED,
                source_image_ref="path/img.png",
                parameters={"key": "value"},
            )
        )
        db_session.commit()

        project_repo.update_status("proj-1", ProjectStatus.IN_PROGRESS)
        db_session.commit()

        result = project_repo.get("proj-1")
        assert result.name == "Original"
        assert result.source_image_ref == "path/img.png"
        assert result.parameters == {"key": "value"}


# --- JSONB round-trip ---


class TestJsonbRoundTrip:
    def test_project_parameters_roundtrip(self, project_repo, db_session):
        params = {"num_colors": 16, "aida_count": 14, "nested": {"a": [1, 2, 3]}}
        project_repo.add(
            Project(
                id="proj-json",
                name="JSON Test",
                created_at=datetime.now(timezone.utc),
                status=ProjectStatus.CREATED,
                source_image_ref=None,
                parameters=params,
            )
        )
        db_session.commit()

        result = project_repo.get("proj-json")
        assert result.parameters == params

    def test_pattern_result_palette_roundtrip(self, project_repo, pattern_repo, db_session):
        project_repo.add(_make_project("proj-1"))
        db_session.commit()

        palette = {"colors": [{"r": 255, "g": 0, "b": 0}, {"r": 0, "g": 255, "b": 0}]}
        pattern_repo.add(
            PatternResult(
                id="pat-1",
                project_id="proj-1",
                created_at=datetime.now(timezone.utc),
                palette=palette,
                grid_width=100,
                grid_height=80,
                stitch_count=8000,
                pdf_ref=None,
            )
        )
        db_session.commit()

        result = pattern_repo.get_latest_by_project("proj-1")
        assert result.palette == palette


# --- PatternResultRepository ---


class TestPatternResultRepositoryCrud:
    def test_add_and_list_by_project(self, project_repo, pattern_repo, db_session):
        project_repo.add(_make_project("proj-1"))
        db_session.commit()

        pattern_repo.add(
            PatternResult(
                id="pat-1",
                project_id="proj-1",
                created_at=datetime.now(timezone.utc),
                palette={},
                grid_width=10,
                grid_height=10,
                stitch_count=100,
                pdf_ref=None,
            )
        )
        db_session.commit()

        results = pattern_repo.list_by_project("proj-1")
        assert len(results) == 1
        assert results[0].id == "pat-1"

    def test_list_by_project_excludes_other_projects(self, project_repo, pattern_repo, db_session):
        project_repo.add(_make_project("proj-1"))
        project_repo.add(_make_project("proj-2", "Other"))
        db_session.commit()

        pattern_repo.add(
            PatternResult(
                id="pat-1",
                project_id="proj-1",
                created_at=datetime.now(timezone.utc),
                palette={},
                grid_width=10,
                grid_height=10,
                stitch_count=100,
                pdf_ref=None,
            )
        )
        pattern_repo.add(
            PatternResult(
                id="pat-2",
                project_id="proj-2",
                created_at=datetime.now(timezone.utc),
                palette={},
                grid_width=10,
                grid_height=10,
                stitch_count=50,
                pdf_ref=None,
            )
        )
        db_session.commit()

        results = pattern_repo.list_by_project("proj-1")
        assert len(results) == 1
        assert results[0].id == "pat-1"

    def test_get_latest_by_project(self, project_repo, pattern_repo, db_session):
        project_repo.add(_make_project("proj-1"))
        db_session.commit()

        t1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        t2 = t1 + timedelta(hours=1)

        pattern_repo.add(
            PatternResult(
                id="pat-old",
                project_id="proj-1",
                created_at=t1,
                palette={},
                grid_width=10,
                grid_height=10,
                stitch_count=100,
                pdf_ref=None,
            )
        )
        pattern_repo.add(
            PatternResult(
                id="pat-new",
                project_id="proj-1",
                created_at=t2,
                palette={},
                grid_width=20,
                grid_height=20,
                stitch_count=400,
                pdf_ref=None,
            )
        )
        db_session.commit()

        result = pattern_repo.get_latest_by_project("proj-1")
        assert result.id == "pat-new"

    def test_get_latest_returns_none_when_empty(self, pattern_repo):
        result = pattern_repo.get_latest_by_project("proj-1")
        assert result is None


# --- FK constraint ---


class TestForeignKeyConstraint:
    def test_pattern_result_requires_existing_project(self, pattern_repo, db_session):
        with pytest.raises(Exception):
            pattern_repo.add(
                PatternResult(
                    id="pat-orphan",
                    project_id="nonexistent",
                    created_at=datetime.now(timezone.utc),
                    palette={},
                    grid_width=10,
                    grid_height=10,
                    stitch_count=100,
                    pdf_ref=None,
                )
            )
            db_session.commit()
