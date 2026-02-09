import pytest
from datetime import datetime, timezone

from app.application.use_cases.save_pattern_result import (
    SavePatternResult,
    SavePatternResultRequest,
)
from app.domain.model.project import Project, ProjectStatus
from app.domain.exceptions import ProjectNotFoundError, DomainException
from tests.helpers.in_memory_repositories import (
    InMemoryProjectRepository,
    InMemoryPatternResultRepository,
)


@pytest.fixture
def project_repo():
    repo = InMemoryProjectRepository()
    repo.add(
        Project(
            id="proj-1",
            name="Test Project",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.IN_PROGRESS,
            source_image_ref=None,
            parameters={},
        )
    )
    return repo


@pytest.fixture
def pattern_repo():
    return InMemoryPatternResultRepository()


@pytest.fixture
def use_case(project_repo, pattern_repo):
    return SavePatternResult(
        project_repo=project_repo,
        pattern_result_repo=pattern_repo,
    )


def test_save_pattern_result_returns_result_with_id(use_case):
    request = SavePatternResultRequest(
        project_id="proj-1",
        palette={"colors": [{"r": 255, "g": 0, "b": 0}]},
        grid_width=100,
        grid_height=80,
        stitch_count=8000,
    )
    result = use_case.execute(request)

    assert result.id is not None
    assert len(result.id) > 0


def test_save_pattern_result_fields_match_request(use_case):
    request = SavePatternResultRequest(
        project_id="proj-1",
        palette={"colors": [{"r": 0, "g": 255, "b": 0}]},
        grid_width=50,
        grid_height=40,
        stitch_count=2000,
        pdf_ref="storage/projects/proj-1/pattern.pdf",
    )
    result = use_case.execute(request)

    assert result.project_id == "proj-1"
    assert result.grid_width == 50
    assert result.grid_height == 40
    assert result.stitch_count == 2000
    assert result.pdf_ref == "storage/projects/proj-1/pattern.pdf"


def test_save_pattern_result_persists_in_repo(use_case, pattern_repo):
    request = SavePatternResultRequest(
        project_id="proj-1",
        palette={},
        grid_width=10,
        grid_height=10,
        stitch_count=100,
    )
    use_case.execute(request)

    stored = pattern_repo.list_by_project("proj-1")
    assert len(stored) == 1
    assert stored[0].stitch_count == 100


def test_save_pattern_result_raises_when_project_not_found(pattern_repo):
    empty_project_repo = InMemoryProjectRepository()
    use_case = SavePatternResult(
        project_repo=empty_project_repo,
        pattern_result_repo=pattern_repo,
    )

    request = SavePatternResultRequest(
        project_id="nonexistent",
        palette={},
        grid_width=10,
        grid_height=10,
        stitch_count=100,
    )
    with pytest.raises(ProjectNotFoundError):
        use_case.execute(request)


def test_save_pattern_result_rejects_invalid_dimensions(use_case):
    with pytest.raises(DomainException, match="grid_width"):
        use_case.execute(
            SavePatternResultRequest(
                project_id="proj-1",
                palette={},
                grid_width=0,
                grid_height=10,
                stitch_count=0,
            )
        )
