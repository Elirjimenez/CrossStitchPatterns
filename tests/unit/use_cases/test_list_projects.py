import pytest
from datetime import datetime, timezone

from app.application.use_cases.list_projects import ListProjects
from app.domain.model.project import Project, ProjectStatus
from tests.helpers.in_memory_repositories import InMemoryProjectRepository


@pytest.fixture
def repo():
    return InMemoryProjectRepository()


@pytest.fixture
def use_case(repo):
    return ListProjects(project_repo=repo)


def _make_project(project_id: str, name: str) -> Project:
    return Project(
        id=project_id,
        name=name,
        created_at=datetime.now(timezone.utc),
        status=ProjectStatus.CREATED,
        source_image_ref=None,
        parameters={},
    )


def test_list_projects_empty_returns_empty_list(use_case):
    result = use_case.execute()

    assert result == []


def test_list_projects_returns_all_projects(use_case, repo):
    repo.add(_make_project("proj-1", "First"))
    repo.add(_make_project("proj-2", "Second"))

    result = use_case.execute()

    assert len(result) == 2
    names = {p.name for p in result}
    assert names == {"First", "Second"}
