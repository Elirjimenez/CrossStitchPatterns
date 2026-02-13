"""Integration tests that run against a real PostgreSQL instance.

These tests validate behaviour that SQLite cannot faithfully reproduce:
JSONB storage, native FK enforcement, CASCADE deletes, and timezone-aware
datetime handling.

Skip automatically when Postgres is not reachable (e.g. CI without Docker).
Run with:  pytest -m postgres -v
"""

import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

from app.domain.model.project import Project, PatternResult, ProjectStatus

pytestmark = pytest.mark.postgres


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _make_pattern_result(
    result_id: str,
    project_id: str,
    created_at: datetime | None = None,
    palette: dict | None = None,
) -> PatternResult:
    return PatternResult(
        id=result_id,
        project_id=project_id,
        created_at=created_at or datetime.now(timezone.utc),
        palette=palette or {},
        grid_width=10,
        grid_height=10,
        stitch_count=100,
        pdf_ref=None,
    )


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


class TestProjectCrudPostgres:
    def test_add_and_get_project(self, pg_project_repo, pg_session):
        pg_project_repo.add(_make_project("proj-1", "Landscape"))
        pg_session.commit()

        result = pg_project_repo.get("proj-1")
        assert result is not None
        assert result.id == "proj-1"
        assert result.name == "Landscape"

    def test_list_all_returns_projects(self, pg_project_repo, pg_session):
        pg_project_repo.add(_make_project("proj-1", "First"))
        pg_project_repo.add(_make_project("proj-2", "Second"))
        pg_session.commit()

        result = pg_project_repo.list_all()
        assert len(result) == 2

    def test_update_status(self, pg_project_repo, pg_session):
        pg_project_repo.add(_make_project("proj-1"))
        pg_session.commit()

        pg_project_repo.update_status("proj-1", ProjectStatus.COMPLETED)
        pg_session.commit()

        result = pg_project_repo.get("proj-1")
        assert result.status == ProjectStatus.COMPLETED


# ---------------------------------------------------------------------------
# JSONB round-trips
# ---------------------------------------------------------------------------


class TestJsonbPostgres:
    def test_project_parameters_jsonb_roundtrip(self, pg_project_repo, pg_session):
        params = {
            "num_colors": 16,
            "aida_count": 14,
            "nested": {"a": [1, 2, 3]},
        }
        pg_project_repo.add(
            Project(
                id="proj-json",
                name="JSON Test",
                created_at=datetime.now(timezone.utc),
                status=ProjectStatus.CREATED,
                source_image_ref=None,
                parameters=params,
            )
        )
        pg_session.commit()

        result = pg_project_repo.get("proj-json")
        assert result.parameters == params

    def test_pattern_result_palette_jsonb_roundtrip(
        self, pg_project_repo, pg_pattern_repo, pg_session
    ):
        pg_project_repo.add(_make_project("proj-1"))
        pg_session.commit()

        palette = {
            "colors": [
                {"r": 255, "g": 0, "b": 0},
                {"r": 0, "g": 255, "b": 0},
            ]
        }
        pg_pattern_repo.add(_make_pattern_result("pat-1", "proj-1", palette=palette))
        pg_session.commit()

        result = pg_pattern_repo.get_latest_by_project("proj-1")
        assert result.palette == palette


# ---------------------------------------------------------------------------
# FK & CASCADE
# ---------------------------------------------------------------------------


class TestForeignKeyPostgres:
    def test_fk_rejects_orphan_pattern_result(self, pg_pattern_repo, pg_session):
        """Postgres must reject a pattern_result whose project_id does not exist."""
        pg_pattern_repo.add(_make_pattern_result("pat-orphan", "nonexistent"))
        with pytest.raises(Exception):
            pg_session.commit()

    def test_cascade_delete_removes_pattern_results(
        self, pg_project_repo, pg_pattern_repo, pg_session
    ):
        """Deleting a project must cascade-delete its pattern_results."""
        pg_project_repo.add(_make_project("proj-1"))
        pg_session.commit()

        pg_pattern_repo.add(_make_pattern_result("pat-1", "proj-1"))
        pg_session.commit()

        pg_session.execute(text("DELETE FROM projects WHERE id = 'proj-1'"))
        pg_session.commit()

        rows = pg_session.execute(
            text("SELECT id FROM pattern_results WHERE project_id = 'proj-1'")
        ).fetchall()
        assert rows == []


# ---------------------------------------------------------------------------
# PatternResult queries
# ---------------------------------------------------------------------------


class TestPatternResultPostgres:
    def test_get_latest_returns_most_recent(self, pg_project_repo, pg_pattern_repo, pg_session):
        pg_project_repo.add(_make_project("proj-1"))
        pg_session.commit()

        t1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        t2 = t1 + timedelta(hours=1)

        pg_pattern_repo.add(_make_pattern_result("pat-old", "proj-1", created_at=t1))
        pg_pattern_repo.add(_make_pattern_result("pat-new", "proj-1", created_at=t2))
        pg_session.commit()

        result = pg_pattern_repo.get_latest_by_project("proj-1")
        assert result.id == "pat-new"

    def test_get_latest_returns_none_when_empty(self, pg_pattern_repo):
        result = pg_pattern_repo.get_latest_by_project("proj-1")
        assert result is None
