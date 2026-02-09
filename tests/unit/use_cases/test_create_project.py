import pytest

from app.application.use_cases.create_project import (
    CreateProject,
    CreateProjectRequest,
)
from app.domain.model.project import ProjectStatus
from app.domain.exceptions import DomainException
from tests.helpers.in_memory_repositories import InMemoryProjectRepository


@pytest.fixture
def repo():
    return InMemoryProjectRepository()


@pytest.fixture
def use_case(repo):
    return CreateProject(project_repo=repo)


def test_create_project_returns_project_with_generated_id(use_case):
    request = CreateProjectRequest(name="Landscape")
    result = use_case.execute(request)

    assert result.id is not None
    assert len(result.id) > 0


def test_create_project_name_matches_request(use_case):
    request = CreateProjectRequest(name="Landscape")
    result = use_case.execute(request)

    assert result.name == "Landscape"


def test_create_project_status_is_created(use_case):
    request = CreateProjectRequest(name="Landscape")
    result = use_case.execute(request)

    assert result.status == ProjectStatus.CREATED


def test_create_project_persists_in_repo(use_case, repo):
    request = CreateProjectRequest(name="My Pattern")
    result = use_case.execute(request)

    stored = repo.get(result.id)
    assert stored is not None
    assert stored.name == "My Pattern"


def test_create_project_with_parameters(use_case, repo):
    request = CreateProjectRequest(
        name="Detailed",
        parameters={"num_colors": 16, "aida_count": 14},
    )
    result = use_case.execute(request)

    stored = repo.get(result.id)
    assert stored.parameters["num_colors"] == 16


def test_create_project_with_source_image_ref(use_case, repo):
    request = CreateProjectRequest(
        name="With Image",
        source_image_ref="storage/projects/abc/source.png",
    )
    result = use_case.execute(request)

    stored = repo.get(result.id)
    assert stored.source_image_ref == "storage/projects/abc/source.png"


def test_create_project_rejects_empty_name(use_case):
    with pytest.raises(DomainException, match="name"):
        use_case.execute(CreateProjectRequest(name=""))
