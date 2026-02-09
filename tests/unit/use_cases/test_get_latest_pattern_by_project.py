import pytest
from datetime import datetime, timezone, timedelta

from app.application.use_cases.get_latest_pattern_by_project import (
    GetLatestPatternByProject,
)
from app.domain.model.project import PatternResult
from tests.helpers.in_memory_repositories import InMemoryPatternResultRepository


@pytest.fixture
def repo():
    return InMemoryPatternResultRepository()


@pytest.fixture
def use_case(repo):
    return GetLatestPatternByProject(pattern_result_repo=repo)


def _make_pattern_result(
    result_id: str,
    project_id: str,
    created_at: datetime,
) -> PatternResult:
    return PatternResult(
        id=result_id,
        project_id=project_id,
        created_at=created_at,
        palette={},
        grid_width=10,
        grid_height=10,
        stitch_count=100,
        pdf_ref=None,
    )


def test_returns_none_when_no_results(use_case):
    result = use_case.execute("proj-1")
    assert result is None


def test_returns_single_result(use_case, repo):
    now = datetime.now(timezone.utc)
    repo.add(_make_pattern_result("pat-1", "proj-1", now))

    result = use_case.execute("proj-1")

    assert result is not None
    assert result.id == "pat-1"


def test_returns_latest_when_multiple(use_case, repo):
    t1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t2 = t1 + timedelta(hours=1)
    t3 = t2 + timedelta(hours=1)

    repo.add(_make_pattern_result("pat-old", "proj-1", t1))
    repo.add(_make_pattern_result("pat-mid", "proj-1", t2))
    repo.add(_make_pattern_result("pat-new", "proj-1", t3))

    result = use_case.execute("proj-1")

    assert result.id == "pat-new"


def test_does_not_return_results_from_other_projects(use_case, repo):
    now = datetime.now(timezone.utc)
    repo.add(_make_pattern_result("pat-other", "proj-other", now))

    result = use_case.execute("proj-1")

    assert result is None
