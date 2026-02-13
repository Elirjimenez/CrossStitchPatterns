import pytest
from datetime import datetime, timezone

from app.domain.model.project import Project, ProjectStatus
from app.application.use_cases.save_pattern_result import (
    SavePatternResult,
    SavePatternResultRequest,
)
from app.infrastructure.storage.local_file_storage import LocalFileStorage
from tests.helpers.in_memory_repositories import (
    InMemoryProjectRepository,
    InMemoryPatternResultRepository,
)


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
def pattern_result_repo():
    return InMemoryPatternResultRepository()


@pytest.fixture
def file_storage(tmp_path):
    return LocalFileStorage(str(tmp_path / "storage"))


class TestCreatePatternWithPdf:
    def test_saves_pdf_and_creates_pattern_result(
        self, project_repo, pattern_result_repo, file_storage
    ):
        project = _make_project()
        project_repo.add(project)

        pdf_data = b"%PDF-1.4 fake pdf content"
        pdf_ref = file_storage.save_pdf(project.id, pdf_data, "pattern.pdf")

        use_case = SavePatternResult(
            project_repo=project_repo, pattern_result_repo=pattern_result_repo
        )
        result = use_case.execute(
            SavePatternResultRequest(
                project_id=project.id,
                palette={"colors": [{"r": 255, "g": 0, "b": 0}]},
                grid_width=100,
                grid_height=80,
                stitch_count=8000,
                pdf_ref=pdf_ref,
            )
        )

        assert result.pdf_ref == pdf_ref
        assert result.project_id == project.id

    def test_pattern_result_fields_match_input(
        self, project_repo, pattern_result_repo, file_storage
    ):
        project = _make_project()
        project_repo.add(project)

        pdf_ref = file_storage.save_pdf(project.id, b"pdf", "pattern.pdf")

        use_case = SavePatternResult(
            project_repo=project_repo, pattern_result_repo=pattern_result_repo
        )
        result = use_case.execute(
            SavePatternResultRequest(
                project_id=project.id,
                palette={"colors": [{"r": 0, "g": 255, "b": 0}]},
                grid_width=50,
                grid_height=40,
                stitch_count=2000,
                pdf_ref=pdf_ref,
            )
        )

        assert result.grid_width == 50
        assert result.grid_height == 40
        assert result.stitch_count == 2000
        assert result.palette == {"colors": [{"r": 0, "g": 255, "b": 0}]}

    def test_project_not_found_raises(self, project_repo, pattern_result_repo):
        use_case = SavePatternResult(
            project_repo=project_repo, pattern_result_repo=pattern_result_repo
        )
        from app.domain.exceptions import ProjectNotFoundError

        with pytest.raises(ProjectNotFoundError):
            use_case.execute(
                SavePatternResultRequest(
                    project_id="nonexistent",
                    palette={},
                    grid_width=10,
                    grid_height=10,
                    stitch_count=100,
                    pdf_ref="some/ref.pdf",
                )
            )

    def test_pdf_stored_on_disk(self, file_storage, tmp_path):
        pdf_data = b"%PDF-1.4 content"
        ref = file_storage.save_pdf("proj-1", pdf_data, "pattern.pdf")

        full_path = tmp_path / "storage" / ref
        assert full_path.exists()
        assert full_path.read_bytes() == pdf_data
