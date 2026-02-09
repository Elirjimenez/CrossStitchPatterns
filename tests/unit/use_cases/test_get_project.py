import pytest
from datetime import datetime, timezone

from app.application.use_cases.get_project import GetProject
from app.domain.model.project import Project, ProjectStatus
from app.domain.exceptions import ProjectNotFoundError
from tests.helpers.in_memory_repositories import InMemoryProjectRepository


@pytest.fixture
def repo():
    return InMemoryProjectRepository()


@pytest.fixture
def use_case(repo):
    return GetProject(project_repo=repo)


def _make_project(project_id: str = "proj-1", name: str = "Test") -> Project:
    return Project(
        id=project_id,
        name=name,
        created_at=datetime.now(timezone.utc),
        status=ProjectStatus.CREATED,
        source_image_ref=None,
        parameters={},
    )


def test_get_project_returns_existing_project(use_case, repo):
    project = _make_project("proj-1", "My Pattern")
    repo.add(project)

    result = use_case.execute("proj-1")

    assert result.id == "proj-1"
    assert result.name == "My Pattern"


def test_get_project_raises_when_not_found(use_case):
    with pytest.raises(ProjectNotFoundError):
        use_case.execute("nonexistent-id")
