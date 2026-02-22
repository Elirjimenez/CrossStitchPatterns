import os
import pytest
from pathlib import Path

from app.application.ports.file_storage import FileStorage
from app.infrastructure.storage.local_file_storage import LocalFileStorage


@pytest.fixture
def base_dir(tmp_path):
    return tmp_path / "storage"


@pytest.fixture
def storage(base_dir) -> FileStorage:
    return LocalFileStorage(base_dir=str(base_dir))


class TestSaveSourceImage:
    def test_returns_relative_ref(self, storage):
        ref = storage.save_source_image("proj-1", b"\x89PNG fake", ".png")

        assert "proj-1" in ref
        assert ref.endswith(".png")

    def test_file_is_written_to_disk(self, storage, base_dir):
        ref = storage.save_source_image("proj-1", b"\x89PNG fake", ".png")

        full_path = base_dir / ref
        assert full_path.exists()
        assert full_path.read_bytes() == b"\x89PNG fake"

    def test_creates_project_directory(self, storage, base_dir):
        storage.save_source_image("proj-2", b"data", ".jpg")

        project_dir = base_dir / "projects" / "proj-2"
        assert project_dir.is_dir()

    def test_overwrites_existing_source(self, storage, base_dir):
        storage.save_source_image("proj-1", b"old", ".png")
        ref = storage.save_source_image("proj-1", b"new", ".png")

        full_path = base_dir / ref
        assert full_path.read_bytes() == b"new"

    def test_normalizes_extension_with_dot(self, storage):
        ref = storage.save_source_image("proj-1", b"data", "png")
        assert ref.endswith(".png")


class TestSaveSourceImageExtensionValidation:
    def test_accepts_png(self, storage):
        ref = storage.save_source_image("proj-1", b"data", ".png")
        assert ref.endswith(".png")

    def test_accepts_jpg(self, storage):
        ref = storage.save_source_image("proj-1", b"data", ".jpg")
        assert ref.endswith(".jpg")

    def test_accepts_jpeg(self, storage):
        ref = storage.save_source_image("proj-1", b"data", ".jpeg")
        assert ref.endswith(".jpeg")

    def test_accepts_gif(self, storage):
        ref = storage.save_source_image("proj-1", b"data", ".gif")
        assert ref.endswith(".gif")

    def test_accepts_webp(self, storage):
        ref = storage.save_source_image("proj-1", b"data", ".webp")
        assert ref.endswith(".webp")

    def test_rejects_exe(self, storage):
        with pytest.raises(ValueError, match="not allowed"):
            storage.save_source_image("proj-1", b"data", ".exe")

    def test_rejects_php(self, storage):
        with pytest.raises(ValueError, match="not allowed"):
            storage.save_source_image("proj-1", b"data", ".php")

    def test_rejects_bin(self, storage):
        with pytest.raises(ValueError, match="not allowed"):
            storage.save_source_image("proj-1", b"data", ".bin")

    def test_rejects_pdf(self, storage):
        # PDFs are not valid source images
        with pytest.raises(ValueError, match="not allowed"):
            storage.save_source_image("proj-1", b"data", ".pdf")

    def test_validation_is_case_insensitive(self, storage):
        # Uppercase extension should still be accepted
        ref = storage.save_source_image("proj-1", b"data", ".PNG")
        assert ref.endswith(".PNG")


class TestSavePdf:
    def test_returns_relative_ref(self, storage):
        ref = storage.save_pdf("proj-1", b"%PDF-1.4 fake", "pattern.pdf")

        assert "proj-1" in ref
        assert ref.endswith("pattern.pdf")

    def test_file_is_written_to_disk(self, storage, base_dir):
        ref = storage.save_pdf("proj-1", b"%PDF content", "result.pdf")

        full_path = base_dir / ref
        assert full_path.exists()
        assert full_path.read_bytes() == b"%PDF content"

    def test_creates_project_directory(self, storage, base_dir):
        storage.save_pdf("proj-3", b"data", "out.pdf")

        project_dir = base_dir / "projects" / "proj-3"
        assert project_dir.is_dir()

    def test_overwrites_existing_pdf(self, storage, base_dir):
        storage.save_pdf("proj-1", b"old pdf", "pattern.pdf")
        ref = storage.save_pdf("proj-1", b"new pdf", "pattern.pdf")

        full_path = base_dir / ref
        assert full_path.read_bytes() == b"new pdf"


class TestReadSourceImage:
    def test_returns_stored_bytes(self, storage):
        ref = storage.save_source_image("proj-1", b"\x89PNG data", ".png")
        data = storage.read_source_image("proj-1", ref)
        assert data == b"\x89PNG data"

    def test_raises_file_not_found_for_missing_ref(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.read_source_image("proj-1", "projects/proj-1/source.png")

    def test_raises_value_error_for_traversal_attempt(self, storage, base_dir):
        with pytest.raises(ValueError):
            storage.read_source_image("proj-1", "../../../etc/passwd")


class TestDeleteProjectFolder:
    def test_deletes_existing_folder(self, storage, base_dir):
        storage.save_source_image("proj-del", b"data", ".png")
        project_dir = base_dir / "projects" / "proj-del"
        assert project_dir.is_dir()

        storage.delete_project_folder("proj-del")

        assert not project_dir.exists()

    def test_no_error_for_missing_folder(self, storage):
        # Must not raise even if the folder has never been created
        storage.delete_project_folder("non-existent-project")

    def test_returns_none(self, storage):
        result = storage.delete_project_folder("any-project")
        assert result is None

    def test_does_not_delete_other_projects(self, storage, base_dir):
        storage.save_source_image("proj-keep", b"keep", ".png")
        storage.save_source_image("proj-del", b"del", ".png")

        storage.delete_project_folder("proj-del")

        assert (base_dir / "projects" / "proj-keep").is_dir()


class TestProtocolCompliance:
    def test_local_file_storage_satisfies_protocol(self, storage):
        assert isinstance(storage, FileStorage)
