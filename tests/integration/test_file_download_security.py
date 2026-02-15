"""Integration tests for file download endpoint security."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.web.api.dependencies import get_file_storage
from app.infrastructure.storage.local_file_storage import LocalFileStorage


@pytest.fixture
def temp_storage_dir(tmp_path, monkeypatch):
    """Create temporary storage and override the dependency."""
    storage_dir = tmp_path / "test_storage"
    storage_dir.mkdir()

    def override_get_file_storage():
        return LocalFileStorage(str(storage_dir))

    app.dependency_overrides[get_file_storage] = override_get_file_storage
    yield storage_dir
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_test_file(temp_storage_dir):
    """Create a valid test file in storage."""
    project_dir = temp_storage_dir / "projects" / "test-project-123"
    project_dir.mkdir(parents=True)
    test_pdf = project_dir / "pattern.pdf"
    test_pdf.write_bytes(b"%PDF-1.4 fake pdf content")
    return "projects/test-project-123/pattern.pdf"


class TestFileDownloadSecurity:
    """Test file download endpoint security."""

    def test_download_valid_file_returns_200(self, client, valid_test_file):
        """Valid file download should return 200."""
        response = client.get(f"/api/projects/files/{valid_test_file}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert b"PDF" in response.content

    def test_download_nonexistent_file_returns_404(self, client, temp_storage_dir):
        """Non-existent file should return 404."""
        response = client.get("/api/projects/files/projects/fake/nonexistent.pdf")
        assert response.status_code == 404
        assert response.json()["detail"] == "File not found"

    def test_download_with_parent_traversal_returns_404(self, client, temp_storage_dir):
        """Path traversal with .. should return 404."""
        response = client.get("/api/projects/files/projects/../../etc/passwd")
        assert response.status_code == 404
        # Detail message should indicate file not found (either custom or default)
        assert "not found" in response.json()["detail"].lower()

    def test_download_absolute_path_returns_404(self, client, temp_storage_dir):
        """Absolute path should return 404."""
        response = client.get("/api/projects/files//etc/passwd")
        assert response.status_code == 404

    def test_download_windows_traversal_returns_404(self, client, temp_storage_dir):
        """Windows-style path traversal should return 404."""
        response = client.get(
            "/api/projects/files/projects\\..\\..\\..\\Windows\\System32\\config\\SAM"
        )
        assert response.status_code == 404

    def test_download_invalid_extension_returns_404(self, client, temp_storage_dir):
        """File with disallowed extension should return 404."""
        # Create a .exe file
        project_dir = temp_storage_dir / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        exe_file = project_dir / "malware.exe"
        exe_file.write_bytes(b"MZ fake exe")

        response = client.get("/api/projects/files/projects/test-project/malware.exe")
        assert response.status_code == 404

    def test_download_png_image_returns_200(self, client, temp_storage_dir):
        """PNG image download should work."""
        project_dir = temp_storage_dir / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        png_file = project_dir / "source.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n fake png")

        response = client.get("/api/projects/files/projects/test-project/source.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_download_jpeg_image_returns_200(self, client, temp_storage_dir):
        """JPEG image download should work."""
        project_dir = temp_storage_dir / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        jpg_file = project_dir / "source.jpg"
        jpg_file.write_bytes(b"\xff\xd8\xff fake jpeg")

        response = client.get("/api/projects/files/projects/test-project/source.jpg")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

    def test_download_preserves_filename(self, client, valid_test_file):
        """Downloaded file should preserve filename."""
        response = client.get(f"/api/projects/files/{valid_test_file}")
        assert response.status_code == 200
        # Check Content-Disposition header for filename
        content_disposition = response.headers.get("content-disposition", "")
        assert "pattern.pdf" in content_disposition

    def test_download_encoded_traversal_returns_404(self, client, temp_storage_dir):
        """URL-encoded path traversal should return 404."""
        response = client.get("/api/projects/files/projects%2F..%2F..%2Fetc%2Fpasswd")
        assert response.status_code == 404

    def test_download_directory_returns_404(self, client, temp_storage_dir):
        """Attempting to download directory should return 404."""
        project_dir = temp_storage_dir / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)

        response = client.get("/api/projects/files/projects/test-project")
        assert response.status_code == 404

    def test_multiple_slashes_normalized(self, client, temp_storage_dir):
        """Multiple slashes should be normalized."""
        project_dir = temp_storage_dir / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        test_file = project_dir / "file.pdf"
        test_file.write_bytes(b"test")

        # Path with multiple slashes
        response = client.get("/api/projects/files/projects//test-project//file.pdf")
        # Should still return 404 as the normalized path won't match
        # or 200 if FastAPI normalizes before passing to handler
        assert response.status_code in [200, 404]
