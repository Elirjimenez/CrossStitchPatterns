"""
Integration tests for HTML web routes (app/web/routes.py).

Covers:
- Task 1: GET /  (home page)
- Task 1: GET /projects  (projects page shell)
- Task 2: GET /hx/projects  (HTMX partial — empty, populated, error states)
- Task 3: POST /hx/projects/create  (create project via HTMX form)
- Task 4: GET /projects/{project_id}  (project detail page)
- Task 5: POST /hx/projects/{project_id}/source-image  (upload source image)
- Task 6: POST /hx/projects/{project_id}/generate  (generate pattern + PDF)
"""

import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.infrastructure.persistence.models.pattern_result_model  # noqa: F401
import app.infrastructure.persistence.models.project_model  # noqa: F401
from app.application.use_cases.complete_existing_project import (
    CompleteExistingProject,
    CompleteExistingProjectResult,
)
from app.domain.exceptions import DomainException, ProjectNotFoundError
from app.domain.model.pattern import Palette, Pattern, PatternGrid
from app.domain.model.project import PatternResult, Project, ProjectStatus
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.persistence.database import Base
from app.infrastructure.storage.local_file_storage import LocalFileStorage
from app.main import create_app
from app.web.api.dependencies import (
    get_complete_existing_project_use_case,
    get_db_session,
    get_file_storage,
    get_pattern_result_repository,
    get_project_repository,
)


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

        def update_source_image_metadata(self, project_id, *, ref, width, height):
            raise RuntimeError("DB unavailable")

        def delete(self, project_id):
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


# ---------------------------------------------------------------------------
# Task 4 — GET /projects/{project_id} (project detail page)
# ---------------------------------------------------------------------------


class TestProjectDetailPage:
    def test_returns_200_for_existing_project(self, client):
        resp = client.post("/api/projects", json={"name": "My Pattern"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert response.status_code == 200

    def test_returns_html(self, client):
        resp = client.post("/api/projects", json={"name": "My Pattern"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert "text/html" in response.headers["content-type"]

    def test_shows_project_name(self, client):
        resp = client.post("/api/projects", json={"name": "Sunset Flowers"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert "Sunset Flowers" in response.text

    def test_shows_project_id(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert project_id in response.text

    def test_shows_status_badge(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert "Created" in response.text

    def test_shows_created_date(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        # Date is formatted as "DD Mon YYYY" e.g. "20 Feb 2026"
        import datetime
        expected_year = str(datetime.datetime.now().year)
        assert expected_year in response.text

    def test_shows_back_to_projects_link(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert 'href="/projects"' in response.text

    def test_shows_no_image_placeholder_when_no_source(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert "No image uploaded" in response.text

    def test_returns_404_for_unknown_project(self, client):
        response = client.get("/projects/does-not-exist")

        assert response.status_code == 404

    def test_404_page_shows_not_found_message(self, client):
        response = client.get("/projects/does-not-exist")

        assert "not found" in response.text.lower()

    def test_404_page_has_back_to_projects_link(self, client):
        response = client.get("/projects/does-not-exist")

        assert 'href="/projects"' in response.text

    def test_repo_error_returns_500(self, error_client):
        response = error_client.get("/projects/any-id")

        assert response.status_code == 500

    def test_detail_page_contains_upload_form(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert f'hx-post="/hx/projects/{project_id}/source-image"' in response.text

    def test_detail_page_contains_source_image_card(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert 'id="source-image-card"' in response.text

    def test_detail_page_has_actions_container(self, client):
        """Detail page must include the HTMX lazy-load container for the Actions panel."""
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert f'hx-get="/hx/projects/{project_id}/actions"' in response.text

    def test_detail_page_has_no_double_slash_urls(self, client):
        """No HTMX URL should contain // (which would mean project_id was empty)."""
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert "projects//" not in response.text

    def test_detail_page_upload_indicator_contains_project_id(self, client):
        """Upload loading indicator element ID must contain the real project_id."""
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/projects/{project_id}")

        assert f'upload-indicator-{project_id}' in response.text


# ---------------------------------------------------------------------------
# Task 5 — POST /hx/projects/{project_id}/source-image (upload source image)
# ---------------------------------------------------------------------------

def _make_image_bytes(fmt: str, width: int = 100, height: int = 80) -> bytes:
    """Generate a minimal valid image in the given PIL format."""
    img = Image.new("RGB", (width, height), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


_FAKE_PNG = _make_image_bytes("PNG")
_FAKE_JPG = _make_image_bytes("JPEG")
_FAKE_WEBP = _make_image_bytes("WEBP")


class TestHxUploadSourceImage:
    def test_valid_png_returns_200(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert response.status_code == 200

    def test_valid_jpeg_returns_200(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.jpg", _FAKE_JPG, "image/jpeg")},
        )

        assert response.status_code == 200

    def test_valid_webp_returns_200(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.webp", _FAKE_WEBP, "image/webp")},
        )

        assert response.status_code == 200

    def test_success_shows_image_uploaded(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert "Image uploaded" in response.text

    def test_success_response_is_html(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert "text/html" in response.headers["content-type"]

    def test_success_response_retains_upload_form(self, client):
        """Card stays interactive after upload so user can replace the image."""
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert f'hx-post="/hx/projects/{project_id}/source-image"' in response.text

    def test_non_image_file_returns_400(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("doc.txt", b"hello", "text/plain")},
        )

        assert response.status_code == 400

    def test_non_image_file_shows_error(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("doc.pdf", b"%PDF", "application/pdf")},
        )

        assert "image" in response.text.lower()

    def test_empty_filename_returns_client_error(self, client):
        """When no file is selected the upload must fail with a 4xx.
        FastAPI's multipart validation (422) or our filename check (400) both satisfy this."""
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("", _FAKE_PNG, "image/png")},
        )

        assert response.status_code in (400, 422)

    def test_unknown_project_returns_404(self, client):
        response = client.post(
            "/hx/projects/no-such-id/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert response.status_code == 404

    def test_unknown_project_shows_error(self, client):
        response = client.post(
            "/hx/projects/no-such-id/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert "not found" in response.text.lower()

    def test_repo_error_returns_500(self, error_client):
        response = error_client.post(
            "/hx/projects/any-id/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert response.status_code == 500

    def test_repo_error_shows_error(self, error_client):
        response = error_client.post(
            "/hx/projects/any-id/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert "error" in response.text.lower()


# ---------------------------------------------------------------------------
# Task 6 — POST /hx/projects/{project_id}/generate (generate pattern + PDF)
# ---------------------------------------------------------------------------

_FAKE_PROJECT_WITH_IMAGE = Project(
    id="p-test-123",
    name="Test Project",
    created_at=datetime(2026, 2, 21, tzinfo=timezone.utc),
    status=ProjectStatus.COMPLETED,
    source_image_ref="projects/p-test-123/source/img.png",
    parameters={},
)

_FAKE_PATTERN = Pattern(
    grid=PatternGrid(width=2, height=2, cells=[[0, 0], [0, 0]]),
    palette=Palette(colors=[(255, 0, 0)]),
)


class _FakeProjectRepoWithImage(ProjectRepository):
    """Minimal project repo that always returns a project with a source image."""

    def get(self, project_id):
        return Project(
            id=project_id,
            name="Test Project",
            created_at=datetime(2026, 2, 21, tzinfo=timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref="projects/p/source/img.png",
            parameters={},
        )

    def add(self, project): pass
    def list_all(self): return []
    def update_status(self, project_id, status): pass
    def update_source_image_ref(self, project_id, ref): pass
    def update_source_image_metadata(self, project_id, *, ref, width, height): pass
    def delete(self, project_id): pass


class _FakeCompleteUseCase:
    """Mock use case that always returns a predictable successful result."""

    def execute(self, request):
        return CompleteExistingProjectResult(
            project=_FAKE_PROJECT_WITH_IMAGE,
            pattern=_FAKE_PATTERN,
            dmc_colors=[],
            pattern_result=PatternResult(
                id="pr-test-123",
                project_id=request.project_id,
                created_at=datetime(2026, 2, 21, 10, 0, 0, tzinfo=timezone.utc),
                palette={"colors": [{"index": i} for i in range(5)]},
                grid_width=80,
                grid_height=60,
                stitch_count=4800,
                pdf_ref=f"projects/{request.project_id}/pdfs/pattern.pdf",
            ),
            pdf_bytes=b"%PDF-1.4 fake",
        )


class _BrokenGenerateUseCase:
    """Mock use case that raises an unexpected RuntimeError."""

    def execute(self, request):
        raise RuntimeError("Internal error from use case")


def _make_generate_client(tmp_path, use_case_instance):
    """Helper to build a TestClient with mocked project repo + use case.

    The repo always returns a project that has a source_image_ref so the
    pre-flight validation in the route passes and we exercise the use case path.
    """
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
    app.dependency_overrides[get_project_repository] = lambda: _FakeProjectRepoWithImage()
    app.dependency_overrides[get_complete_existing_project_use_case] = (
        lambda: use_case_instance
    )
    return TestClient(app)


@pytest.fixture
def generate_client(tmp_path):
    """TestClient with mocked repo + use case that always succeeds."""
    return _make_generate_client(tmp_path, _FakeCompleteUseCase())


@pytest.fixture
def broken_generate_client(tmp_path):
    """TestClient with mocked repo + use case that raises an unexpected error."""
    return _make_generate_client(tmp_path, _BrokenGenerateUseCase())


class TestHxGeneratePattern:
    """Task 6: POST /hx/projects/{project_id}/generate"""

    # --- Success path ---

    def test_success_returns_200(self, generate_client):
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert response.status_code == 200

    def test_success_returns_html(self, generate_client):
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "text/html" in response.headers["content-type"]

    def test_success_shows_pattern_dimensions(self, generate_client):
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "80" in response.text
        assert "60" in response.text

    def test_success_shows_stitch_count(self, generate_client):
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "4800" in response.text

    def test_success_shows_colors_count(self, generate_client):
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "5" in response.text

    def test_success_shows_pdf_download_link(self, generate_client):
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "/api/projects/files/" in response.text

    def test_success_shows_success_indicator(self, generate_client):
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "success" in response.text.lower() or "generated" in response.text.lower()

    def test_success_response_contains_results_card_id(self, generate_client):
        """Response must include the swappable card ID so HTMX can update it."""
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert 'id="pattern-results-card"' in response.text

    def test_default_params_accepted(self, generate_client):
        """Route must work when only num_colors is posted (others have defaults)."""
        response = generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10"},
        )

        assert response.status_code == 200

    # --- Validation: numeric parameters ---

    def test_num_colors_below_min_returns_400(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "1", "target_width": "80", "target_height": "80"},
        )

        assert response.status_code == 400

    def test_num_colors_below_min_shows_error(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "1", "target_width": "80", "target_height": "80"},
        )

        assert "color" in response.text.lower()

    def test_num_colors_above_max_returns_400(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "101", "target_width": "80", "target_height": "80"},
        )

        assert response.status_code == 400

    def test_target_width_below_min_returns_400(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "10", "target_width": "5", "target_height": "80"},
        )

        assert response.status_code == 400

    def test_target_width_above_max_returns_400(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "10", "target_width": "501", "target_height": "80"},
        )

        assert response.status_code == 400

    def test_target_height_below_min_returns_400(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "5"},
        )

        assert response.status_code == 400

    def test_target_height_above_max_returns_400(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "501"},
        )

        assert response.status_code == 400

    def test_invalid_param_response_contains_results_card_id(self, client):
        response = client.post(
            "/hx/projects/any-id/generate",
            data={"num_colors": "0", "target_width": "80", "target_height": "80"},
        )

        assert 'id="pattern-results-card"' in response.text

    # --- Validation: project state ---

    def test_project_not_found_returns_404(self, client):
        """project_id that does not exist in the DB must return 404."""
        response = client.post(
            "/hx/projects/no-such-id/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert response.status_code == 404

    def test_project_not_found_shows_error(self, client):
        response = client.post(
            "/hx/projects/no-such-id/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "not found" in response.text.lower()

    def test_no_source_image_returns_400(self, client):
        """Project exists but has no source_image_ref must return 400."""
        resp = client.post("/api/projects", json={"name": "No Image"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert response.status_code == 400

    def test_no_source_image_shows_message(self, client):
        resp = client.post("/api/projects", json={"name": "No Image"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "image" in response.text.lower()

    # --- Error: unexpected failure ---

    def test_unexpected_error_returns_500(self, broken_generate_client):
        response = broken_generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert response.status_code == 500

    def test_unexpected_error_shows_error_message(self, broken_generate_client):
        response = broken_generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert "error" in response.text.lower()

    def test_unexpected_error_contains_results_card_id(self, broken_generate_client):
        response = broken_generate_client.post(
            "/hx/projects/p-test-123/generate",
            data={"num_colors": "10", "target_width": "80", "target_height": "80"},
        )

        assert 'id="pattern-results-card"' in response.text


# ---------------------------------------------------------------------------
# Task 7 — Image dimension extraction and form prefill
# ---------------------------------------------------------------------------


class TestImageDimensionExtraction:
    """Source image dimensions are extracted at upload time and prefill the generate form."""

    def test_corrupt_image_returns_400(self, client):
        """Bytes that look like an image MIME type but are unreadable must be rejected."""
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 20, "image/png")},
        )

        assert response.status_code == 400

    def test_corrupt_image_shows_error(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 20, "image/png")},
        )

        assert "image" in response.text.lower()

    def test_upload_persists_dimensions(self, client):
        """After uploading a 100×80 image the actions partial must reflect those dimensions."""
        resp = client.post("/api/projects", json={"name": "Dim Test"})
        project_id = resp.json()["id"]
        png_bytes = _make_image_bytes("PNG", width=100, height=80)

        client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", png_bytes, "image/png")},
        )

        actions = client.get(f"/hx/projects/{project_id}/actions")
        assert 'value="100"' in actions.text
        assert 'value="80"' in actions.text

    def test_detail_page_prefills_stored_dimensions(self, client):
        """Generate form target_width/height must use the uploaded image dimensions."""
        resp = client.post("/api/projects", json={"name": "Prefill Test"})
        project_id = resp.json()["id"]
        png_bytes = _make_image_bytes("PNG", width=200, height=150)

        client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", png_bytes, "image/png")},
        )

        actions = client.get(f"/hx/projects/{project_id}/actions")
        assert 'value="200"' in actions.text
        assert 'value="150"' in actions.text

    def test_detail_page_clamps_large_dimensions_to_500(self, client):
        """Dimensions larger than 500 must be clamped to 500 in the actions form defaults."""
        resp = client.post("/api/projects", json={"name": "Big Image"})
        project_id = resp.json()["id"]
        png_bytes = _make_image_bytes("PNG", width=800, height=600)

        client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", png_bytes, "image/png")},
        )

        actions = client.get(f"/hx/projects/{project_id}/actions")
        # Both should be clamped; value="800" and value="600" must NOT appear
        assert 'value="800"' not in actions.text
        assert 'value="600"' not in actions.text
        assert 'value="500"' in actions.text

    def test_detail_page_no_image_defaults_to_300(self, client):
        """When no image has been uploaded the actions defaults remain 300×300."""
        resp = client.post("/api/projects", json={"name": "No Image"})
        project_id = resp.json()["id"]

        actions = client.get(f"/hx/projects/{project_id}/actions")

        # value="300" must appear at least twice (width and height)
        assert actions.text.count('value="300"') >= 2


# ---------------------------------------------------------------------------
# Fix: GET /hx/projects/{project_id}/actions (lazy-loaded Actions panel)
# ---------------------------------------------------------------------------


class TestHxProjectActions:
    """GET /hx/projects/{project_id}/actions — Actions panel partial."""

    def test_returns_200_for_existing_project(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert response.status_code == 200

    def test_returns_html(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert "text/html" in response.headers["content-type"]

    def test_contains_generate_form(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert f'hx-post="/hx/projects/{project_id}/generate"' in response.text

    def test_contains_target_width_input(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert 'name="target_width"' in response.text

    def test_contains_target_height_input(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert 'name="target_height"' in response.text

    def test_generate_button_disabled_without_source_image(self, client):
        """Button shows cursor-not-allowed styling when no image has been uploaded."""
        resp = client.post("/api/projects", json={"name": "No Image"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert "cursor-not-allowed" in response.text

    def test_generate_button_enabled_with_source_image(self, client):
        """Button shows active (indigo) styling when an image is present."""
        resp = client.post("/api/projects", json={"name": "With Image"})
        project_id = resp.json()["id"]
        client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert "cursor-not-allowed" not in response.text
        assert "bg-indigo-600" in response.text

    def test_defaults_to_image_dimensions_when_uploaded(self, client):
        resp = client.post("/api/projects", json={"name": "Sized"})
        project_id = resp.json()["id"]
        png_bytes = _make_image_bytes("PNG", width=160, height=120)
        client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", png_bytes, "image/png")},
        )

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert 'value="160"' in response.text
        assert 'value="120"' in response.text

    def test_defaults_to_300_fallback_without_image(self, client):
        resp = client.post("/api/projects", json={"name": "Fallback"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert response.text.count('value="300"') >= 2

    def test_contains_self_refresh_trigger_attribute(self, client):
        """The returned partial must re-register itself so future actions:refresh events work."""
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert f'hx-get="/hx/projects/{project_id}/actions"' in response.text

    def test_generate_loading_indicator_contains_project_id(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.get(f"/hx/projects/{project_id}/actions")

        assert f"generate-loading-{project_id}" in response.text

    def test_returns_404_for_unknown_project(self, client):
        response = client.get("/hx/projects/no-such-project/actions")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Fix: upload success triggers Actions panel refresh via HX-Trigger header
# ---------------------------------------------------------------------------


class TestUploadActionsRefreshTrigger:
    """POST /hx/projects/{project_id}/source-image — HX-Trigger on success."""

    def test_success_sets_hx_trigger_header(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert "HX-Trigger" in response.headers

    def test_success_trigger_contains_actions_refresh(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert "actions:refresh" in response.headers.get("HX-Trigger", "")

    def test_error_non_image_does_not_set_trigger(self, client):
        resp = client.post("/api/projects", json={"name": "Any"})
        project_id = resp.json()["id"]

        response = client.post(
            f"/hx/projects/{project_id}/source-image",
            files={"file": ("doc.txt", b"hello", "text/plain")},
        )

        assert "actions:refresh" not in response.headers.get("HX-Trigger", "")

    def test_error_unknown_project_does_not_set_trigger(self, client):
        response = client.post(
            "/hx/projects/no-such-id/source-image",
            files={"file": ("photo.png", _FAKE_PNG, "image/png")},
        )

        assert "actions:refresh" not in response.headers.get("HX-Trigger", "")


# ---------------------------------------------------------------------------
# Delete Project — DELETE /hx/projects/{project_id}
# ---------------------------------------------------------------------------


class _InProgressProjectRepo(ProjectRepository):
    """Returns a project with IN_PROGRESS status for any ID (simulate mid-generation)."""

    def get(self, project_id):
        return Project(
            id=project_id,
            name="Busy Project",
            created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            status=ProjectStatus.IN_PROGRESS,
            source_image_ref=None,
            parameters={},
        )

    def add(self, project): pass
    def list_all(self): return []
    def update_status(self, project_id, status): pass
    def update_source_image_ref(self, project_id, ref): pass
    def update_source_image_metadata(self, project_id, *, ref, width, height): pass
    def delete(self, project_id): pass


class _NoOpPatternResultRepo(PatternResultRepository):
    def add(self, pattern_result): pass
    def list_by_project(self, project_id): return []
    def get_latest_by_project(self, project_id): return None
    def delete_by_project(self, project_id): pass


@pytest.fixture
def in_progress_delete_client(tmp_path):
    """TestClient whose project repo always returns an IN_PROGRESS project."""
    storage = LocalFileStorage(str(tmp_path / "storage"))
    app = create_app()
    app.dependency_overrides[get_project_repository] = lambda: _InProgressProjectRepo()
    app.dependency_overrides[get_pattern_result_repository] = lambda: _NoOpPatternResultRepo()
    app.dependency_overrides[get_file_storage] = lambda: storage
    return TestClient(app)


class TestHxDeleteProject:
    """DELETE /hx/projects/{project_id}"""

    def test_delete_existing_project_returns_hx_redirect(self, client):
        resp = client.post("/api/projects", json={"name": "ToDelete"})
        project_id = resp.json()["id"]

        response = client.delete(f"/hx/projects/{project_id}")

        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/projects"

    def test_delete_existing_project_removes_from_db(self, client):
        resp = client.post("/api/projects", json={"name": "ToDelete"})
        project_id = resp.json()["id"]

        client.delete(f"/hx/projects/{project_id}")

        detail = client.get(f"/projects/{project_id}")
        assert detail.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        response = client.delete("/hx/projects/no-such-id")

        assert response.status_code == 404

    def test_delete_nonexistent_shows_error(self, client):
        response = client.delete("/hx/projects/no-such-id")

        assert "not found" in response.text.lower()

    def test_delete_in_progress_returns_409(self, in_progress_delete_client):
        response = in_progress_delete_client.delete("/hx/projects/any-id")

        assert response.status_code == 409

    def test_delete_in_progress_shows_message(self, in_progress_delete_client):
        response = in_progress_delete_client.delete("/hx/projects/any-id")

        text = response.text.lower()
        assert "progress" in text or "processing" in text or "processed" in text

    def test_delete_button_present_in_detail_page(self, client):
        resp = client.post("/api/projects", json={"name": "HasButton"})
        project_id = resp.json()["id"]

        detail = client.get(f"/projects/{project_id}")

        assert f'hx-delete="/hx/projects/{project_id}"' in detail.text

    def test_delete_also_removes_pattern_results(self, client):
        """Pattern results for the project must be gone after deletion."""
        resp = client.post("/api/projects", json={"name": "WithResults"})
        project_id = resp.json()["id"]

        client.delete(f"/hx/projects/{project_id}")

        # Project is gone — detail page must return 404
        assert client.get(f"/projects/{project_id}").status_code == 404
