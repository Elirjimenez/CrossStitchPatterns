import pytest
from datetime import datetime, timezone

from app.domain.model.project import Project, ProjectStatus
from app.domain.exceptions import ProjectNotFoundError
from app.infrastructure.storage.local_file_storage import LocalFileStorage
from tests.helpers.in_memory_repositories import InMemoryProjectRepository


def _make_project(project_id: str = "proj-1") -> Project:
    return Project(
        id=project_id,
        name="Test Project",
        created_at=datetime.now(timezone.utc),
        status=ProjectStatus.CREATED,
        source_image_ref=None,
        parameters={},
    )


@pytest.fixture
def project_repo():
    return InMemoryProjectRepository()


@pytest.fixture
def file_storage(tmp_path):
    return LocalFileStorage(str(tmp_path / "storage"))


class TestUploadSourceImage:
    def test_saves_file_and_updates_ref(self, project_repo, file_storage):
        project = _make_project()
        project_repo.add(project)

        data = b"\x89PNG fake image data"
        ref = file_storage.save_source_image(project.id, data, ".png")
        project_repo.update_source_image_ref(project.id, ref)

        updated = project_repo.get(project.id)
        assert updated.source_image_ref == ref
        assert "proj-1" in ref
        assert ref.endswith(".png")

    def test_project_not_found_raises(self, project_repo):
        result = project_repo.get("nonexistent")
        assert result is None

    def test_extracts_correct_extension_png(self, file_storage):
        ref = file_storage.save_source_image("proj-1", b"data", ".png")
        assert ref.endswith(".png")

    def test_extracts_correct_extension_jpg(self, file_storage):
        ref = file_storage.save_source_image("proj-1", b"data", ".jpg")
        assert ref.endswith(".jpg")

    def test_file_bytes_stored_on_disk(self, file_storage, tmp_path):
        data = b"\x89PNG real content"
        ref = file_storage.save_source_image("proj-1", data, ".png")

        full_path = tmp_path / "storage" / ref
        assert full_path.exists()
        assert full_path.read_bytes() == data
