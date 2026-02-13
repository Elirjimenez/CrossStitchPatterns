import json

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.persistence.database import Base
from app.infrastructure.storage.local_file_storage import LocalFileStorage
import app.infrastructure.persistence.models.project_model  # noqa: F401
import app.infrastructure.persistence.models.pattern_result_model  # noqa: F401
from app.main import create_app
from app.web.api.dependencies import get_db_session, get_file_storage


@pytest.fixture
def client(tmp_path):
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

    storage_dir = tmp_path / "storage"
    storage = LocalFileStorage(str(storage_dir))

    app = create_app()
    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_file_storage] = lambda: storage
    return TestClient(app)


# --- POST /api/projects ---


class TestCreateProject:
    def test_create_project_returns_201(self, client):
        response = client.post("/api/projects", json={"name": "My Pattern"})

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Pattern"
        assert data["status"] == "created"
        assert data["id"] is not None

    def test_create_project_with_parameters(self, client):
        response = client.post(
            "/api/projects",
            json={"name": "Detailed", "parameters": {"num_colors": 16}},
        )

        assert response.status_code == 201
        assert response.json()["parameters"]["num_colors"] == 16

    def test_create_project_rejects_empty_name(self, client):
        response = client.post("/api/projects", json={"name": ""})
        assert response.status_code == 422


# --- GET /api/projects ---


class TestListProjects:
    def test_list_projects_empty(self, client):
        response = client.get("/api/projects")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects_returns_created(self, client):
        client.post("/api/projects", json={"name": "First"})
        client.post("/api/projects", json={"name": "Second"})

        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


# --- GET /api/projects/{id} ---


class TestGetProject:
    def test_get_project(self, client):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        project_id = create_resp.json()["id"]

        response = client.get(f"/api/projects/{project_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_get_project_not_found(self, client):
        response = client.get("/api/projects/nonexistent")
        assert response.status_code == 400


# --- PATCH /api/projects/{id}/status ---


class TestUpdateProjectStatus:
    def test_update_status(self, client):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        project_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/projects/{project_id}/status",
            json={"status": "in_progress"},
        )
        assert response.status_code == 204

        get_resp = client.get(f"/api/projects/{project_id}")
        assert get_resp.json()["status"] == "in_progress"

    def test_update_status_invalid_value(self, client):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        project_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/projects/{project_id}/status",
            json={"status": "invalid"},
        )
        assert response.status_code == 422


# --- POST /api/projects/{id}/patterns ---


class TestCreatePatternResult:
    def test_create_pattern_result(self, client):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        project_id = create_resp.json()["id"]

        response = client.post(
            f"/api/projects/{project_id}/patterns",
            json={
                "palette": {"colors": [{"r": 255, "g": 0, "b": 0}]},
                "grid_width": 100,
                "grid_height": 80,
                "stitch_count": 8000,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == project_id
        assert data["grid_width"] == 100
        assert data["stitch_count"] == 8000

    def test_create_pattern_result_project_not_found(self, client):
        response = client.post(
            "/api/projects/nonexistent/patterns",
            json={
                "palette": {},
                "grid_width": 10,
                "grid_height": 10,
                "stitch_count": 100,
            },
        )
        assert response.status_code == 400


# --- POST /api/projects/{id}/source-image ---


class TestUploadSourceImage:
    def test_upload_source_image(self, client):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        project_id = create_resp.json()["id"]

        response = client.post(
            f"/api/projects/{project_id}/source-image",
            files={"file": ("photo.png", b"\x89PNG fake", "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_image_ref"] is not None
        assert data["source_image_ref"].endswith(".png")

    def test_upload_source_image_project_not_found(self, client):
        response = client.post(
            "/api/projects/nonexistent/source-image",
            files={"file": ("photo.png", b"\x89PNG fake", "image/png")},
        )
        assert response.status_code == 400

    def test_upload_source_image_no_file(self, client):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        project_id = create_resp.json()["id"]

        response = client.post(f"/api/projects/{project_id}/source-image")
        assert response.status_code == 422


# --- POST /api/projects/{id}/patterns/with-pdf ---


class TestCreatePatternResultWithPdf:
    def test_create_pattern_with_pdf(self, client):
        create_resp = client.post("/api/projects", json={"name": "Test"})
        project_id = create_resp.json()["id"]

        palette_json = json.dumps({"colors": [{"r": 255, "g": 0, "b": 0}]})
        response = client.post(
            f"/api/projects/{project_id}/patterns/with-pdf",
            files={"file": ("pattern.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={
                "palette": palette_json,
                "grid_width": "100",
                "grid_height": "80",
                "stitch_count": "8000",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == project_id
        assert data["pdf_ref"] is not None
        assert data["grid_width"] == 100

    def test_create_pattern_with_pdf_project_not_found(self, client):
        response = client.post(
            "/api/projects/nonexistent/patterns/with-pdf",
            files={"file": ("pattern.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={
                "palette": "{}",
                "grid_width": "10",
                "grid_height": "10",
                "stitch_count": "100",
            },
        )
        assert response.status_code == 400
