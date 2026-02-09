import pytest
from datetime import datetime, timezone

from app.domain.model.project import Project, PatternResult, ProjectStatus
from app.domain.exceptions import DomainException


# --- ProjectStatus ---


def test_project_status_values():
    assert ProjectStatus.CREATED.value == "created"
    assert ProjectStatus.IN_PROGRESS.value == "in_progress"
    assert ProjectStatus.COMPLETED.value == "completed"
    assert ProjectStatus.FAILED.value == "failed"


# --- Project entity ---


def test_project_creation():
    now = datetime.now(timezone.utc)
    project = Project(
        id="proj-1",
        name="My Pattern",
        created_at=now,
        status=ProjectStatus.CREATED,
        source_image_ref=None,
        parameters={},
    )
    assert project.id == "proj-1"
    assert project.name == "My Pattern"
    assert project.created_at == now
    assert project.status == ProjectStatus.CREATED
    assert project.source_image_ref is None
    assert project.parameters == {}


def test_project_with_parameters():
    project = Project(
        id="proj-2",
        name="Landscape",
        created_at=datetime.now(timezone.utc),
        status=ProjectStatus.IN_PROGRESS,
        source_image_ref="storage/projects/proj-2/source.png",
        parameters={"num_colors": 16, "aida_count": 14},
    )
    assert project.source_image_ref == "storage/projects/proj-2/source.png"
    assert project.parameters["num_colors"] == 16


def test_project_is_immutable():
    project = Project(
        id="proj-1",
        name="Test",
        created_at=datetime.now(timezone.utc),
        status=ProjectStatus.CREATED,
        source_image_ref=None,
        parameters={},
    )
    with pytest.raises(AttributeError):
        project.name = "Changed"


def test_project_name_must_not_be_empty():
    with pytest.raises(DomainException, match="name"):
        Project(
            id="proj-1",
            name="",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )


def test_project_name_must_not_be_blank():
    with pytest.raises(DomainException, match="name"):
        Project(
            id="proj-1",
            name="   ",
            created_at=datetime.now(timezone.utc),
            status=ProjectStatus.CREATED,
            source_image_ref=None,
            parameters={},
        )


# --- PatternResult entity ---


def test_pattern_result_creation():
    now = datetime.now(timezone.utc)
    result = PatternResult(
        id="pat-1",
        project_id="proj-1",
        created_at=now,
        palette={"colors": [{"r": 255, "g": 0, "b": 0}]},
        grid_width=100,
        grid_height=80,
        stitch_count=8000,
        pdf_ref=None,
    )
    assert result.id == "pat-1"
    assert result.project_id == "proj-1"
    assert result.grid_width == 100
    assert result.grid_height == 80
    assert result.stitch_count == 8000
    assert result.pdf_ref is None


def test_pattern_result_is_immutable():
    result = PatternResult(
        id="pat-1",
        project_id="proj-1",
        created_at=datetime.now(timezone.utc),
        palette={},
        grid_width=10,
        grid_height=10,
        stitch_count=100,
        pdf_ref=None,
    )
    with pytest.raises(AttributeError):
        result.grid_width = 50


def test_pattern_result_grid_width_must_be_positive():
    with pytest.raises(DomainException, match="grid_width"):
        PatternResult(
            id="pat-1",
            project_id="proj-1",
            created_at=datetime.now(timezone.utc),
            palette={},
            grid_width=0,
            grid_height=10,
            stitch_count=0,
            pdf_ref=None,
        )


def test_pattern_result_grid_height_must_be_positive():
    with pytest.raises(DomainException, match="grid_height"):
        PatternResult(
            id="pat-1",
            project_id="proj-1",
            created_at=datetime.now(timezone.utc),
            palette={},
            grid_width=10,
            grid_height=0,
            stitch_count=0,
            pdf_ref=None,
        )


def test_pattern_result_stitch_count_must_not_be_negative():
    with pytest.raises(DomainException, match="stitch_count"):
        PatternResult(
            id="pat-1",
            project_id="proj-1",
            created_at=datetime.now(timezone.utc),
            palette={},
            grid_width=10,
            grid_height=10,
            stitch_count=-1,
            pdf_ref=None,
        )
