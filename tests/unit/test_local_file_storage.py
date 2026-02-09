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


class TestProtocolCompliance:
    def test_local_file_storage_satisfies_protocol(self, storage):
        assert isinstance(storage, FileStorage)
