import pytest
from datetime import datetime, timezone

from app.application.use_cases.update_project_status import UpdateProjectStatus
from app.domain.model.project import Project, ProjectStatus
from app.domain.exceptions import ProjectNotFoundError
from tests.helpers.in_memory_repositories import InMemoryProjectRepository


@pytest.fixture
def repo():
    return InMemoryProjectRepository()


@pytest.fixture
def use_case(repo):
    return UpdateProjectStatus(project_repo=repo)


def _make_project(project_id: str = "proj-1") -> Project:
    return Project(
        id=project_id,
        name="Test",
        created_at=datetime.now(timezone.utc),
        status=ProjectStatus.CREATED,
        source_image_ref=None,
        parameters={},
    )


def test_update_status_changes_project_status(use_case, repo):
    repo.add(_make_project("proj-1"))

    use_case.execute("proj-1", ProjectStatus.IN_PROGRESS)

    updated = repo.get("proj-1")
    assert updated.status == ProjectStatus.IN_PROGRESS


def test_update_status_preserves_other_fields(use_case, repo):
    project = Project(
        id="proj-1",
        name="Original Name",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        status=ProjectStatus.CREATED,
        source_image_ref="some/path.png",
        parameters={"key": "value"},
    )
    repo.add(project)

    use_case.execute("proj-1", ProjectStatus.COMPLETED)

    updated = repo.get("proj-1")
    assert updated.name == "Original Name"
    assert updated.source_image_ref == "some/path.png"
    assert updated.parameters == {"key": "value"}


def test_update_status_raises_when_not_found(use_case):
    with pytest.raises(ProjectNotFoundError):
        use_case.execute("nonexistent", ProjectStatus.FAILED)
