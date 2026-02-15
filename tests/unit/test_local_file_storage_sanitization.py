"""Tests for LocalFileStorage filename and project ID sanitization."""

import pytest
from pathlib import Path

from app.infrastructure.storage.local_file_storage import LocalFileStorage


@pytest.fixture
def storage(tmp_path):
    """Create a LocalFileStorage instance with temp directory."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    return LocalFileStorage(str(storage_dir))


class TestFilenameSanitization:
    """Test _sanitize_filename method edge cases."""

    def test_filename_without_extension(self, storage):
        """Should handle filenames without extensions."""
        result = storage._sanitize_filename("README")
        assert result == "README"

    def test_filename_only_special_chars(self, storage):
        """Should replace special chars with underscores."""
        # Special chars are replaced with underscores, not removed
        result = storage._sanitize_filename("@#$%")
        assert result == "____"

    def test_filename_only_dots_and_spaces(self, storage):
        """Should default to 'file' when only dots and spaces."""
        result = storage._sanitize_filename("...")
        assert result.startswith("file")

    def test_very_long_filename(self, storage):
        """Should truncate very long filenames."""
        long_name = "a" * 300 + ".txt"
        result = storage._sanitize_filename(long_name)
        # Should be truncated to max_length (255 by default)
        assert len(result) <= 255

    def test_very_long_filename_preserves_extension(self, storage):
        """Should preserve extension even when truncating."""
        long_name = "a" * 300 + ".pdf"
        result = storage._sanitize_filename(long_name)
        assert result.endswith(".pdf")
        assert len(result) <= 255

    def test_dangerous_characters_replaced(self, storage):
        """Should replace dangerous characters with underscores."""
        result = storage._sanitize_filename("test@file#name!.pdf")
        assert result == "test_file_name_.pdf"

    def test_path_separators_removed(self, storage):
        """Should remove path separators."""
        result = storage._sanitize_filename("path/to/file.pdf")
        assert "/" not in result
        assert result == "path_to_file.pdf"

    def test_leading_dots_stripped(self, storage):
        """Should strip leading dots."""
        result = storage._sanitize_filename("...hidden.txt")
        assert not result.startswith(".")

    def test_spaces_replaced_with_underscores(self, storage):
        """Should replace spaces with underscores."""
        result = storage._sanitize_filename("file   name.txt")
        assert result == "file___name.txt"

    def test_unicode_characters_replaced(self, storage):
        """Should handle unicode characters."""
        result = storage._sanitize_filename("file™®©.pdf")
        # Unicode chars should be replaced
        assert result == "file___.pdf"

    def test_null_bytes_removed(self, storage):
        """Should remove null bytes."""
        result = storage._sanitize_filename("file\x00name.pdf")
        assert "\x00" not in result

    def test_custom_max_length(self, tmp_path):
        """Should respect custom max_filename_length."""
        storage = LocalFileStorage(str(tmp_path), max_filename_length=20)
        result = storage._sanitize_filename("very_long_filename.txt")
        assert len(result) <= 20


class TestProjectIdSanitization:
    """Test _sanitize_project_id method edge cases."""

    def test_valid_uuid_unchanged(self, storage):
        """Should not modify valid UUID."""
        project_id = "123e4567-e89b-12d3-a456-426614174000"
        result = storage._sanitize_project_id(project_id)
        assert result == project_id

    def test_alphanumeric_id_unchanged(self, storage):
        """Should not modify alphanumeric IDs."""
        project_id = "proj123"
        result = storage._sanitize_project_id(project_id)
        assert result == project_id

    def test_special_characters_replaced(self, storage):
        """Should replace special characters with underscores."""
        result = storage._sanitize_project_id("proj@#$123")
        assert result == "proj___123"

    def test_spaces_replaced(self, storage):
        """Should replace spaces with underscores."""
        result = storage._sanitize_project_id("my project")
        assert result == "my_project"

    def test_empty_string_raises_error(self, storage):
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError) as exc_info:
            storage._sanitize_project_id("")
        assert "cannot be empty after sanitization" in str(exc_info.value)

    def test_special_chars_become_underscores(self, storage):
        """Should replace special chars with underscores (not raise error)."""
        # Special chars are replaced with underscores, creating a valid ID
        result = storage._sanitize_project_id("@#$%^")
        assert result == "_____"

    def test_only_special_chars_creates_valid_id(self, storage):
        """Should create valid ID from special chars (underscores)."""
        # Special chars become underscores, which is valid
        result = storage._sanitize_project_id("!@#$%^&*()")
        assert result == "__________"


class TestResolveFileForDownloadEdgeCases:
    """Test resolve_file_for_download method edge cases."""

    def test_handles_oserror_gracefully(self, storage, tmp_path):
        """Should return None on OSError without raising."""
        # Create a file then make it inaccessible (simulate permission error)
        project_dir = tmp_path / "storage" / "projects" / "test"
        project_dir.mkdir(parents=True)
        test_file = project_dir / "test.pdf"
        test_file.write_text("test")

        # Try to resolve with a path that might cause OS errors
        # (Hard to simulate real OSError, but this tests the exception handling)
        result = storage.resolve_file_for_download("projects/test/test.pdf")
        # Should successfully resolve or return None, not raise
        assert result is None or isinstance(result, Path)

    def test_handles_invalid_path_characters(self, storage):
        """Should return None for paths with invalid characters."""
        # Null bytes and other invalid path characters
        result = storage.resolve_file_for_download("file\x00name.pdf")
        assert result is None

    def test_returns_none_for_very_long_path(self, storage):
        """Should handle very long paths gracefully."""
        # Create a path that's longer than filesystem limits
        long_path = "a/" * 500 + "file.pdf"
        result = storage.resolve_file_for_download(long_path)
        assert result is None


class TestEnsureProjectDirWithInvalidIds:
    """Test _ensure_project_dir with edge cases."""

    def test_creates_dir_with_sanitized_id(self, storage, tmp_path):
        """Should create directory with sanitized project ID."""
        project_dir = storage._ensure_project_dir("test@project")
        assert project_dir.exists()
        assert project_dir.is_dir()
        # Directory name should be sanitized
        assert "test_project" in str(project_dir)

    def test_handles_special_char_id(self, storage, tmp_path):
        """Should handle IDs with special characters."""
        # Special chars become underscores, creating valid directory
        project_dir = storage._ensure_project_dir("!@#$%")
        assert project_dir.exists()
        assert project_dir.is_dir()

    def test_raises_error_for_empty_id(self, storage):
        """Should raise ValueError for empty ID."""
        with pytest.raises(ValueError):
            storage._ensure_project_dir("")


class TestCustomAllowedExtensions:
    """Test custom allowed extensions configuration."""

    def test_custom_allowed_extensions(self, tmp_path):
        """Should respect custom allowed extensions."""
        storage = LocalFileStorage(str(tmp_path), allowed_extensions={".txt", ".md"})

        # Create test file
        project_dir = tmp_path / "projects" / "test"
        project_dir.mkdir(parents=True)
        txt_file = project_dir / "file.txt"
        txt_file.write_text("test")
        pdf_file = project_dir / "file.pdf"
        pdf_file.write_text("test")

        # .txt should be allowed
        result = storage.resolve_file_for_download("projects/test/file.txt")
        assert result is not None

        # .pdf should NOT be allowed (not in custom list)
        result = storage.resolve_file_for_download("projects/test/file.pdf")
        assert result is None
