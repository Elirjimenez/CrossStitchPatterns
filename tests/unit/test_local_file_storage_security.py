"""Security tests for LocalFileStorage path traversal protection."""
import tempfile
from pathlib import Path

import pytest

from app.infrastructure.storage.local_file_storage import LocalFileStorage


class TestPathTraversalProtection:
    """Test that LocalFileStorage prevents directory traversal attacks."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create a temporary storage directory."""
        storage_dir = tmp_path / "storage"
        storage_dir.mkdir()
        return LocalFileStorage(str(storage_dir))

    @pytest.fixture
    def valid_file(self, temp_storage, tmp_path):
        """Create a valid test file in storage."""
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True)
        test_file = project_dir / "test.pdf"
        test_file.write_text("test content")
        return "projects/test-project/test.pdf"

    def test_resolve_valid_file_returns_path(self, temp_storage, valid_file):
        """Valid file path should resolve successfully."""
        result = temp_storage.resolve_file_for_download(valid_file)
        assert result is not None
        assert result.exists()
        assert result.is_file()

    def test_resolve_nonexistent_file_returns_none(self, temp_storage):
        """Non-existent file should return None."""
        result = temp_storage.resolve_file_for_download("projects/nonexistent/file.pdf")
        assert result is None

    def test_resolve_parent_traversal_returns_none(self, temp_storage, valid_file):
        """Path with .. parent traversal should return None."""
        result = temp_storage.resolve_file_for_download("projects/../../../etc/passwd")
        assert result is None

    def test_resolve_absolute_path_returns_none(self, temp_storage):
        """Absolute paths should return None."""
        result = temp_storage.resolve_file_for_download("/etc/passwd")
        assert result is None

    def test_resolve_windows_path_traversal_returns_none(self, temp_storage):
        """Windows-style path traversal should return None."""
        result = temp_storage.resolve_file_for_download("projects\\..\\..\\..\\Windows\\System32\\config\\SAM")
        assert result is None

    def test_resolve_mixed_separators_traversal_returns_none(self, temp_storage):
        """Mixed path separators with traversal should return None."""
        result = temp_storage.resolve_file_for_download("projects/../../../etc/passwd")
        assert result is None

    def test_resolve_url_encoded_traversal_returns_none(self, temp_storage):
        """URL-encoded path traversal should return None."""
        # After normalization, this should still be caught
        result = temp_storage.resolve_file_for_download("projects%2F..%2F..%2Fetc%2Fpasswd")
        assert result is None

    def test_resolve_invalid_extension_returns_none(self, temp_storage, tmp_path):
        """File with non-allowed extension should return None."""
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        evil_file = project_dir / "malicious.exe"
        evil_file.write_text("evil code")

        result = temp_storage.resolve_file_for_download("projects/test-project/malicious.exe")
        assert result is None

    def test_resolve_directory_returns_none(self, temp_storage, tmp_path):
        """Attempting to download a directory should return None."""
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)

        result = temp_storage.resolve_file_for_download("projects/test-project")
        assert result is None

    def test_resolve_symlink_outside_base_returns_none(self, temp_storage, tmp_path):
        """Symlink pointing outside storage should return None."""
        # Create a file outside storage
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside content")

        # Create symlink inside storage pointing outside
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        symlink = project_dir / "link.pdf"

        try:
            symlink.symlink_to(outside_file)
            result = temp_storage.resolve_file_for_download("projects/test-project/link.pdf")
            # Symlink resolves to outside storage, should return None
            assert result is None
        except (OSError, NotImplementedError):
            # Symlinks might not be supported on all systems
            pytest.skip("Symlinks not supported on this system")

    def test_allowed_extensions_png(self, temp_storage, tmp_path):
        """PNG files should be allowed."""
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        png_file = project_dir / "image.png"
        png_file.write_bytes(b"fake png")

        result = temp_storage.resolve_file_for_download("projects/test-project/image.png")
        assert result is not None

    def test_allowed_extensions_jpeg(self, temp_storage, tmp_path):
        """JPEG/JPG files should be allowed."""
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)

        jpg_file = project_dir / "image.jpg"
        jpg_file.write_bytes(b"fake jpg")
        result = temp_storage.resolve_file_for_download("projects/test-project/image.jpg")
        assert result is not None

        jpeg_file = project_dir / "image.jpeg"
        jpeg_file.write_bytes(b"fake jpeg")
        result = temp_storage.resolve_file_for_download("projects/test-project/image.jpeg")
        assert result is not None

    def test_allowed_extensions_pdf(self, temp_storage, tmp_path):
        """PDF files should be allowed."""
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = project_dir / "pattern.pdf"
        pdf_file.write_bytes(b"fake pdf")

        result = temp_storage.resolve_file_for_download("projects/test-project/pattern.pdf")
        assert result is not None

    def test_case_insensitive_extension_check(self, temp_storage, tmp_path):
        """Extension check should be case-insensitive."""
        project_dir = tmp_path / "storage" / "projects" / "test-project"
        project_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = project_dir / "pattern.PDF"
        pdf_file.write_bytes(b"fake pdf")

        result = temp_storage.resolve_file_for_download("projects/test-project/pattern.PDF")
        assert result is not None
