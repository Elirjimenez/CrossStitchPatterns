"""Integration tests for the complete pattern creation workflow endpoint."""

import io

import pytest
from PIL import Image
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
    """Create a test client with in-memory database and temporary file storage."""
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


def create_test_image(width: int, height: int) -> bytes:
    """Create a simple test image in PNG format."""
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestCompletePatternWorkflow:
    def test_creates_complete_pattern_returns_201(self, client):
        """The endpoint should create a complete pattern and return 201."""
        image_data = create_test_image(20, 15)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "My Pattern",
                "target_width": "20",
                "target_height": "15",
                "num_colors": "5",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "project" in data
        assert "pattern_result" in data
        assert "pdf_url" in data

    def test_project_has_completed_status(self, client):
        """The created project should have COMPLETED status."""
        image_data = create_test_image(10, 10)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "Test",
                "target_width": "10",
                "target_height": "10",
                "num_colors": "3",
            },
        )

        assert response.status_code == 201
        project = response.json()["project"]
        assert project["status"] == "completed"
        assert project["name"] == "Test"

    def test_project_has_source_image_ref(self, client):
        """The created project should have a source image reference."""
        image_data = create_test_image(10, 10)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("photo.jpg", image_data, "image/jpeg")},
            data={
                "name": "Test",
                "target_width": "10",
                "target_height": "10",
                "num_colors": "3",
            },
        )

        assert response.status_code == 201
        project = response.json()["project"]
        assert project["source_image_ref"] is not None
        assert ".jpg" in project["source_image_ref"]

    def test_pattern_result_has_pdf_ref(self, client):
        """The pattern result should have a PDF reference."""
        image_data = create_test_image(10, 10)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "Test",
                "target_width": "10",
                "target_height": "10",
                "num_colors": "3",
            },
        )

        assert response.status_code == 201
        pattern_result = response.json()["pattern_result"]
        assert pattern_result["pdf_ref"] is not None
        assert "pattern.pdf" in pattern_result["pdf_ref"]

    def test_pattern_result_has_correct_dimensions(self, client):
        """The pattern result should have the requested dimensions."""
        image_data = create_test_image(25, 30)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "Test",
                "target_width": "25",
                "target_height": "30",
                "num_colors": "4",
            },
        )

        assert response.status_code == 201
        pattern_result = response.json()["pattern_result"]
        assert pattern_result["grid_width"] == 25
        assert pattern_result["grid_height"] == 30

    def test_uses_custom_fabric_parameters(self, client):
        """The endpoint should accept custom aida_count, num_strands, and margin."""
        image_data = create_test_image(10, 10)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "Test",
                "target_width": "10",
                "target_height": "10",
                "num_colors": "3",
                "aida_count": "18",
                "num_strands": "1",
                "margin_cm": "10.0",
            },
        )

        assert response.status_code == 201
        project = response.json()["project"]
        assert project["parameters"]["aida_count"] == 18
        assert project["parameters"]["num_strands"] == 1
        assert project["parameters"]["margin_cm"] == 10.0

    def test_validates_required_fields(self, client):
        """The endpoint should validate required fields."""
        image_data = create_test_image(10, 10)

        # Missing name
        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "target_width": "10",
                "target_height": "10",
                "num_colors": "3",
            },
        )
        assert response.status_code == 422

    def test_validates_positive_dimensions(self, client):
        """The endpoint should reject non-positive dimensions."""
        image_data = create_test_image(10, 10)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "Test",
                "target_width": "0",  # Invalid
                "target_height": "10",
                "num_colors": "3",
            },
        )
        assert response.status_code == 422

    def test_validates_num_strands_range(self, client):
        """The endpoint should validate num_strands is between 1 and 6."""
        image_data = create_test_image(10, 10)

        response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "Test",
                "target_width": "10",
                "target_height": "10",
                "num_colors": "3",
                "num_strands": "7",  # Invalid (> 6)
            },
        )
        assert response.status_code == 422

    def test_project_appears_in_list(self, client):
        """The created project should appear in the projects list."""
        image_data = create_test_image(10, 10)

        # Create complete pattern
        create_response = client.post(
            "/api/projects/complete",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "name": "List Test",
                "target_width": "10",
                "target_height": "10",
                "num_colors": "3",
            },
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["project"]["id"]

        # List projects
        list_response = client.get("/api/projects")
        assert list_response.status_code == 200
        projects = list_response.json()
        assert len(projects) == 1
        assert projects[0]["id"] == project_id
        assert projects[0]["status"] == "completed"
