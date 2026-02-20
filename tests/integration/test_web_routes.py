"""
Integration tests for HTML web routes (app/web/routes.py).

Covers:
- Task 1: GET /  (home page)
- Task 1: GET /projects  (projects page shell)
- Task 2: GET /hx/projects  (HTMX partial — empty, populated, error states)
- Task 3: POST /hx/projects/create  (create project via HTMX form)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.infrastructure.persistence.models.pattern_result_model  # noqa: F401
import app.infrastructure.persistence.models.project_model  # noqa: F401
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.persistence.database import Base
from app.infrastructure.storage.local_file_storage import LocalFileStorage
from app.main import create_app
from app.web.api.dependencies import get_db_session, get_file_storage, get_project_repository


# ---------------------------------------------------------------------------
# Shared fixture: in-memory SQLite + dependency overrides
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    """TestClient wired to an in-memory SQLite DB (mirrors test_projects_api pattern)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def _override_session():
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    storage = LocalFileStorage(str(tmp_path / "storage"))
    app = create_app()
    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_file_storage] = lambda: storage
    return TestClient(app)


@pytest.fixture
def error_client(tmp_path):
    """TestClient whose project repository always raises, to test error state."""

    class _BrokenRepo(ProjectRepository):
        def add(self, project):
            raise RuntimeError("DB unavailable")

        def get(self, project_id):
            raise RuntimeError("DB unavailable")

        def list_all(self):
            raise RuntimeError("DB unavailable")

        def update_status(self, project_id, status):
            raise RuntimeError("DB unavailable")

        def update_source_image_ref(self, project_id, ref):
            raise RuntimeError("DB unavailable")

    storage = LocalFileStorage(str(tmp_path / "storage"))
    app = create_app()
    app.dependency_overrides[get_project_repository] = lambda: _BrokenRepo()
    app.dependency_overrides[get_file_storage] = lambda: storage
    return TestClient(app)


# ---------------------------------------------------------------------------
# Task 1 — GET / (home page)
# ---------------------------------------------------------------------------


class TestHomePage:
    def test_returns_200(self, client):
        response = client.get("/")

        assert response.status_code == 200

    def test_returns_html(self, client):
        response = client.get("/")

        assert "text/html" in response.headers["content-type"]

    def test_contains_app_title(self, client):
        response = client.get("/")

        assert "Cross-Stitch Pattern Generator" in response.text

    def test_contains_view_projects_link(self, client):
        response = client.get("/")

        assert "/projects" in response.text

    def test_contains_navbar(self, client):
        response = client.get("/")

        assert "Home" in response.text
        assert "Projects" in response.text


# ---------------------------------------------------------------------------
# Task 1 — GET /projects (page shell)
# ---------------------------------------------------------------------------


class TestProjectsPage:
    def test_returns_200(self, client):
        response = client.get("/projects")

        assert response.status_code == 200

    def test_returns_html(self, client):
        response = client.get("/projects")

        assert "text/html" in response.headers["content-type"]

    def test_contains_page_heading(self, client):
        response = client.get("/projects")

        assert "Projects" in response.text

    def test_contains_htmx_trigger(self, client):
        """The projects list container must declare hx-get and listen for projectsChanged."""
        response = client.get("/projects")

        assert 'hx-get="/hx/projects"' in response.text
        assert "projectsChanged" in response.text

    def test_contains_htmx_target(self, client):
        response = client.get("/projects")

        assert 'id="projects-list"' in response.text


# ---------------------------------------------------------------------------
# Task 3 — GET /projects (form)
# ---------------------------------------------------------------------------


class TestProjectsPageForm:
    def test_contains_create_form(self, client):
        response = client.get("/projects")

        assert 'hx-post="/hx/projects/create"' in response.text

    def test_form_has_name_input(self, client):
        response = client.get("/projects")

        assert 'name="name"' in response.text

    def test_form_targets_feedback_div(self, client):
        response = client.get("/projects")

        assert 'hx-target="#project-form-feedback"' in response.text

    def test_contains_feedback_div(self, client):
        response = client.get("/projects")

        assert 'id="project-form-feedback"' in response.text


# ---------------------------------------------------------------------------
# Task 2 — GET /hx/projects (HTMX partial)
# ---------------------------------------------------------------------------


class TestHxProjectsEmpty:
    def test_returns_200(self, client):
        response = client.get("/hx/projects")

        assert response.status_code == 200

    def test_returns_html(self, client):
        response = client.get("/hx/projects")

        assert "text/html" in response.headers["content-type"]

    def test_shows_empty_state(self, client):
        response = client.get("/hx/projects")

        assert "No projects yet" in response.text

    def test_empty_state_has_home_link(self, client):
        response = client.get("/hx/projects")

        assert 'href="/"' in response.text


class TestHxProjectsPopulated:
    def test_shows_project_name(self, client):
        client.post("/api/projects", json={"name": "Sunflower Pattern"})

        response = client.get("/hx/projects")

        assert "Sunflower Pattern" in response.text

    def test_shows_created_status_badge(self, client):
        client.post("/api/projects", json={"name": "Rose"})

        response = client.get("/hx/projects")

        assert "Created" in response.text

    def test_shows_all_projects(self, client):
        client.post("/api/projects", json={"name": "Project Alpha"})
        client.post("/api/projects", json={"name": "Project Beta"})

        response = client.get("/hx/projects")

        assert "Project Alpha" in response.text
        assert "Project Beta" in response.text

    def test_shows_completed_status_badge(self, client):
        resp = client.post("/api/projects", json={"name": "Done"})
        project_id = resp.json()["id"]
        client.patch(f"/api/projects/{project_id}/status", json={"status": "completed"})

        response = client.get("/hx/projects")

        assert "Completed" in response.text

    def test_shows_in_progress_status_badge(self, client):
        resp = client.post("/api/projects", json={"name": "WIP"})
        project_id = resp.json()["id"]
        client.patch(f"/api/projects/{project_id}/status", json={"status": "in_progress"})

        response = client.get("/hx/projects")

        assert "In Progress" in response.text

    def test_project_row_contains_detail_link(self, client):
        resp = client.post("/api/projects", json={"name": "Linked"})
        project_id = resp.json()["id"]

        response = client.get("/hx/projects")

        assert f"/projects/{project_id}" in response.text


class TestHxProjectsError:
    def test_returns_200_on_repository_failure(self, error_client):
        """Error state must return 200 so HTMX renders the partial normally."""
        response = error_client.get("/hx/projects")

        assert response.status_code == 200

    def test_shows_error_message(self, error_client):
        response = error_client.get("/hx/projects")

        assert "Could not load projects" in response.text

    def test_shows_retry_button(self, error_client):
        response = error_client.get("/hx/projects")

        assert "Retry" in response.text

    def test_retry_button_targets_hx_endpoint(self, error_client):
        response = error_client.get("/hx/projects")

        assert 'hx-get="/hx/projects"' in response.text


# ---------------------------------------------------------------------------
# Task 3 — POST /hx/projects/create
# ---------------------------------------------------------------------------


class TestHxCreateProject:
    def test_valid_name_returns_200(self, client):
        response = client.post("/hx/projects/create", data={"name": "My Project"})

        assert response.status_code == 200

    def test_valid_name_shows_success_message(self, client):
        response = client.post("/hx/projects/create", data={"name": "My Project"})

        assert "My Project" in response.text

    def test_valid_name_sets_hx_trigger_header(self, client):
        response = client.post("/hx/projects/create", data={"name": "My Project"})

        assert "HX-Trigger" in response.headers
        assert "projectsChanged" in response.headers["HX-Trigger"]

    def test_valid_name_persists_project(self, client):
        client.post("/hx/projects/create", data={"name": "Persisted"})

        list_response = client.get("/hx/projects")

        assert "Persisted" in list_response.text

    def test_empty_name_returns_400(self, client):
        response = client.post("/hx/projects/create", data={"name": ""})

        assert response.status_code == 400

    def test_empty_name_shows_error(self, client):
        response = client.post("/hx/projects/create", data={"name": ""})

        assert "required" in response.text.lower()

    def test_whitespace_name_returns_400(self, client):
        response = client.post("/hx/projects/create", data={"name": "   "})

        assert response.status_code == 400

    def test_missing_name_returns_400(self, client):
        response = client.post("/hx/projects/create", data={})

        assert response.status_code == 400

    def test_repo_error_returns_500(self, error_client):
        response = error_client.post("/hx/projects/create", data={"name": "Test"})

        assert response.status_code == 500

    def test_repo_error_shows_error_message(self, error_client):
        response = error_client.post("/hx/projects/create", data={"name": "Test"})

        assert "error" in response.text.lower()
