import pytest
from datetime import datetime, timezone

from app.domain.model.project import Project, PatternResult, ProjectStatus
from app.infrastructure.persistence.models.project_model import ProjectModel
from app.infrastructure.persistence.models.pattern_result_model import PatternResultModel
from app.infrastructure.persistence.mappers.project_mapper import ProjectMapper
from app.infrastructure.persistence.mappers.pattern_result_mapper import PatternResultMapper


class TestProjectMapper:
    def test_to_model(self):
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        domain = Project(
            id="proj-1",
            name="Landscape",
            created_at=now,
            status=ProjectStatus.IN_PROGRESS,
            source_image_ref="projects/proj-1/source.png",
            parameters={"num_colors": 16, "aida_count": 14},
        )

        model = ProjectMapper.to_model(domain)

        assert model.id == "proj-1"
        assert model.name == "Landscape"
        assert model.created_at == now
        assert model.status == "in_progress"
        assert model.source_image_ref == "projects/proj-1/source.png"
        assert model.parameters == {"num_colors": 16, "aida_count": 14}

    def test_to_domain(self):
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        model = ProjectModel(
            id="proj-2",
            name="Portrait",
            created_at=now,
            status="completed",
            source_image_ref=None,
            parameters={},
        )

        domain = ProjectMapper.to_domain(model)

        assert domain.id == "proj-2"
        assert domain.name == "Portrait"
        assert domain.created_at == now
        assert domain.status == ProjectStatus.COMPLETED
        assert domain.source_image_ref is None
        assert domain.parameters == {}

    def test_roundtrip_preserves_data(self):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        original = Project(
            id="proj-rt",
            name="Roundtrip",
            created_at=now,
            status=ProjectStatus.CREATED,
            source_image_ref="path/to/img.jpg",
            parameters={"key": "value"},
        )

        model = ProjectMapper.to_model(original)
        restored = ProjectMapper.to_domain(model)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.created_at == original.created_at
        assert restored.status == original.status
        assert restored.source_image_ref == original.source_image_ref
        assert restored.parameters == original.parameters


class TestPatternResultMapper:
    def test_to_model(self):
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        domain = PatternResult(
            id="pat-1",
            project_id="proj-1",
            created_at=now,
            palette={"colors": [{"r": 255, "g": 0, "b": 0}]},
            grid_width=100,
            grid_height=80,
            stitch_count=8000,
            pdf_ref="projects/proj-1/pattern.pdf",
        )

        model = PatternResultMapper.to_model(domain)

        assert model.id == "pat-1"
        assert model.project_id == "proj-1"
        assert model.created_at == now
        assert model.palette == {"colors": [{"r": 255, "g": 0, "b": 0}]}
        assert model.grid_width == 100
        assert model.grid_height == 80
        assert model.stitch_count == 8000
        assert model.pdf_ref == "projects/proj-1/pattern.pdf"

    def test_to_domain(self):
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        model = PatternResultModel(
            id="pat-2",
            project_id="proj-1",
            created_at=now,
            palette={},
            grid_width=50,
            grid_height=40,
            stitch_count=2000,
            pdf_ref=None,
        )

        domain = PatternResultMapper.to_domain(model)

        assert domain.id == "pat-2"
        assert domain.project_id == "proj-1"
        assert domain.grid_width == 50
        assert domain.grid_height == 40
        assert domain.stitch_count == 2000
        assert domain.pdf_ref is None

    def test_roundtrip_preserves_data(self):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        original = PatternResult(
            id="pat-rt",
            project_id="proj-1",
            created_at=now,
            palette={"colors": [{"r": 0, "g": 255, "b": 0}]},
            grid_width=200,
            grid_height=150,
            stitch_count=30000,
            pdf_ref="some/path.pdf",
        )

        model = PatternResultMapper.to_model(original)
        restored = PatternResultMapper.to_domain(model)

        assert restored.id == original.id
        assert restored.project_id == original.project_id
        assert restored.created_at == original.created_at
        assert restored.palette == original.palette
        assert restored.grid_width == original.grid_width
        assert restored.grid_height == original.grid_height
        assert restored.stitch_count == original.stitch_count
        assert restored.pdf_ref == original.pdf_ref
