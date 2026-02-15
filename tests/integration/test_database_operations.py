"""
Smoke tests for database operations against PostgreSQL.

These tests validate that the core database operations work correctly with
a real PostgreSQL database, including:
- Connection and schema creation
- Basic CRUD operations
- Transaction handling
- Foreign key constraints
- JSONB column storage
- Cascading deletes

Run with PostgreSQL:
    docker-compose -f docker/docker-compose.test.yml up -d
    pytest tests/integration/test_database_operations.py -v
    docker-compose -f docker/docker-compose.test.yml down

Or run all PostgreSQL tests:
    pytest -m postgres -v
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import text

from app.domain.model.project import Project, PatternResult, ProjectStatus
from app.domain.exceptions import ProjectNotFoundError

pytestmark = pytest.mark.postgres


class TestDatabaseConnection:
    """Smoke tests for basic database connectivity."""

    def test_can_connect_to_database(self, pg_session):
        """The test should be able to connect to PostgreSQL."""
        result = pg_session.execute(text("SELECT 1 as value")).fetchone()
        assert result[0] == 1

    def test_database_version_is_postgres(self, pg_session):
        """The database should be PostgreSQL, not SQLite."""
        result = pg_session.execute(text("SELECT version()")).fetchone()
        version_string = result[0]
        assert "PostgreSQL" in version_string

    def test_tables_are_created(self, pg_session):
        """The database schema should have the required tables."""
        result = pg_session.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        ).fetchall()

        table_names = [row[0] for row in result]
        assert "projects" in table_names
        assert "pattern_results" in table_names


class TestProjectCRUD:
    """Smoke tests for Project repository CRUD operations."""

    def test_create_and_retrieve_project(self, pg_project_repo, pg_session):
        """Should be able to create and retrieve a project."""
        project = Project(
            id="test-proj-1",
            name="Test Pattern",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={"num_colors": 5},
        )

        pg_project_repo.add(project)
        pg_session.commit()

        retrieved = pg_project_repo.get("test-proj-1")
        assert retrieved is not None
        assert retrieved.id == "test-proj-1"
        assert retrieved.name == "Test Pattern"
        assert retrieved.status == ProjectStatus.CREATED

    def test_list_projects(self, pg_project_repo, pg_session):
        """Should be able to list all projects."""
        project1 = Project(
            id="proj-1",
            name="First",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )
        project2 = Project(
            id="proj-2",
            name="Second",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.COMPLETED,
            source_image_ref=None,
            parameters={},
        )

        pg_project_repo.add(project1)
        pg_project_repo.add(project2)
        pg_session.commit()

        projects = pg_project_repo.list_all()
        assert len(projects) == 2

    def test_update_project_status(self, pg_project_repo, pg_session):
        """Should be able to update project status."""
        project = Project(
            id="proj-update",
            name="Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )

        pg_project_repo.add(project)
        pg_session.commit()

        pg_project_repo.update_status("proj-update", ProjectStatus.IN_PROGRESS)
        pg_session.commit()

        updated = pg_project_repo.get("proj-update")
        assert updated.status == ProjectStatus.IN_PROGRESS


class TestPatternResultCRUD:
    """Smoke tests for PatternResult repository operations."""

    def test_create_pattern_result(self, pg_project_repo, pg_pattern_repo, pg_session):
        """Should be able to create a pattern result linked to a project."""
        # Create project first
        project = Project(
            id="proj-with-pattern",
            name="Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )
        pg_project_repo.add(project)
        pg_session.commit()

        # Create pattern result
        pattern_result = PatternResult(
            id="pattern-1",
            project_id="proj-with-pattern",
            created_at=datetime.now(timezone.utc),
            palette={"colors": [{"r": 255, "g": 0, "b": 0}]},
            grid_width=50,
            grid_height=40,
            stitch_count=2000,
            pdf_ref="pdfs/test.pdf",
        )
        pg_pattern_repo.add(pattern_result)
        pg_session.commit()

        # Retrieve
        retrieved = pg_pattern_repo.get_latest_by_project("proj-with-pattern")
        assert retrieved is not None
        assert retrieved.id == "pattern-1"
        assert retrieved.grid_width == 50
        assert retrieved.grid_height == 40


class TestTransactionHandling:
    """Smoke tests for transaction rollback and commit."""

    def test_rollback_on_error(self, pg_project_repo, pg_session):
        """Changes should be rolled back on error."""
        project = Project(
            id="proj-rollback",
            name="Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )

        pg_project_repo.add(project)
        # Don't commit - rollback
        pg_session.rollback()

        # Project should not exist
        retrieved = pg_project_repo.get("proj-rollback")
        assert retrieved is None

    def test_commit_persists_changes(self, pg_project_repo, pg_session):
        """Committed changes should persist."""
        project = Project(
            id="proj-commit",
            name="Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )

        pg_project_repo.add(project)
        pg_session.commit()

        # Create new session to verify persistence
        pg_session.expire_all()
        retrieved = pg_project_repo.get("proj-commit")
        assert retrieved is not None


class TestJSONBStorage:
    """Smoke tests for JSONB column storage (PostgreSQL-specific)."""

    def test_project_parameters_stored_as_jsonb(self, pg_project_repo, pg_session):
        """Project parameters should be stored as JSONB and retrieved correctly."""
        complex_params = {
            "num_colors": 10,
            "aida_count": 14,
            "nested": {
                "key": "value",
                "list": [1, 2, 3],
                "bool": True,
            },
        }

        project = Project(
            id="proj-jsonb",
            name="Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters=complex_params,
        )

        pg_project_repo.add(project)
        pg_session.commit()

        retrieved = pg_project_repo.get("proj-jsonb")
        assert retrieved.parameters == complex_params
        assert retrieved.parameters["nested"]["list"] == [1, 2, 3]

    def test_pattern_palette_stored_as_jsonb(self, pg_project_repo, pg_pattern_repo, pg_session):
        """Pattern palette should be stored as JSONB."""
        project = Project(
            id="proj-palette",
            name="Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )
        pg_project_repo.add(project)
        pg_session.commit()

        palette = {
            "colors": [
                {"r": 255, "g": 0, "b": 0},
                {"r": 0, "g": 255, "b": 0},
                {"r": 0, "g": 0, "b": 255},
            ],
            "dmc_colors": [
                {"number": "310", "name": "Black"},
                {"number": "B5200", "name": "Snow White"},
            ],
        }

        pattern_result = PatternResult(
            id="pattern-palette",
            project_id="proj-palette",
            created_at=datetime.now(timezone.utc),
            palette=palette,
            grid_width=10,
            grid_height=10,
            stitch_count=100,
            pdf_ref=None,
        )
        pg_pattern_repo.add(pattern_result)
        pg_session.commit()

        retrieved = pg_pattern_repo.get_latest_by_project("proj-palette")
        assert retrieved.palette == palette


class TestForeignKeyConstraints:
    """Smoke tests for foreign key constraint enforcement."""

    def test_cannot_create_pattern_without_project(self, pg_pattern_repo, pg_session):
        """Should not be able to create a pattern result for non-existent project."""
        pattern_result = PatternResult(
            id="orphan-pattern",
            project_id="nonexistent-project",
            created_at=datetime.now(timezone.utc),
            palette={},
            grid_width=10,
            grid_height=10,
            stitch_count=100,
            pdf_ref=None,
        )

        pg_pattern_repo.add(pattern_result)

        # Should raise an integrity error on commit
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            pg_session.commit()

    def test_cascade_delete_removes_pattern_results(
        self, pg_project_repo, pg_pattern_repo, pg_session
    ):
        """Deleting a project should cascade delete its pattern results."""
        # Create project with pattern
        project = Project(
            id="proj-cascade",
            name="Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )
        pg_project_repo.add(project)
        pg_session.commit()

        pattern_result = PatternResult(
            id="pattern-cascade",
            project_id="proj-cascade",
            created_at=datetime.now(timezone.utc),
            palette={},
            grid_width=10,
            grid_height=10,
            stitch_count=100,
            pdf_ref=None,
        )
        pg_pattern_repo.add(pattern_result)
        pg_session.commit()

        # Delete project (should cascade to pattern_results)
        pg_session.execute(text("DELETE FROM projects WHERE id = 'proj-cascade'"))
        pg_session.commit()

        # Pattern result should be gone
        result = pg_session.execute(
            text("SELECT * FROM pattern_results WHERE project_id = 'proj-cascade'")
        ).fetchall()
        assert len(result) == 0


class TestCompleteWorkflow:
    """Smoke test for complete pattern creation workflow."""

    def test_end_to_end_pattern_creation(self, pg_project_repo, pg_pattern_repo, pg_session):
        """
        Smoke test for complete workflow:
        1. Create project
        2. Update source image ref
        3. Update status to IN_PROGRESS
        4. Create pattern result
        5. Update status to COMPLETED
        """
        # Step 1: Create project
        project = Project(
            id="e2e-proj",
            name="End-to-End Test",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={"num_colors": 5, "aida_count": 14},
        )
        pg_project_repo.add(project)
        pg_session.commit()

        # Step 2: Update source image ref
        pg_project_repo.update_source_image_ref("e2e-proj", "images/test.png")
        pg_session.commit()

        # Step 3: Update status to IN_PROGRESS
        pg_project_repo.update_status("e2e-proj", ProjectStatus.IN_PROGRESS)
        pg_session.commit()

        # Step 4: Create pattern result
        pattern_result = PatternResult(
            id="e2e-pattern",
            project_id="e2e-proj",
            created_at=datetime.now(timezone.utc),
            palette={"colors": [{"r": 255, "g": 0, "b": 0}]},
            grid_width=50,
            grid_height=50,
            stitch_count=2500,
            pdf_ref="pdfs/e2e-test.pdf",
        )
        pg_pattern_repo.add(pattern_result)
        pg_session.commit()

        # Step 5: Update status to COMPLETED
        pg_project_repo.update_status("e2e-proj", ProjectStatus.COMPLETED)
        pg_session.commit()

        # Verify final state
        final_project = pg_project_repo.get("e2e-proj")
        assert final_project.status == ProjectStatus.COMPLETED
        assert final_project.source_image_ref == "images/test.png"

        final_pattern = pg_pattern_repo.get_latest_by_project("e2e-proj")
        assert final_pattern is not None
        assert final_pattern.pdf_ref == "pdfs/e2e-test.pdf"
