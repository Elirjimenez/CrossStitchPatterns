"""Tests for CompleteExistingProject use case (TDD)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, call

from app.application.use_cases.complete_existing_project import (
    CompleteExistingProject,
    CompleteExistingProjectRequest,
    CompleteExistingProjectResult,
)
from app.domain.exceptions import DomainException, ProjectNotFoundError
from app.domain.model.project import Project, ProjectStatus
from datetime import datetime, timezone


def _make_project(source_image_ref="projects/proj-1/source.png"):
    return Project(
        id="proj-1",
        name="My Project",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        status=ProjectStatus.CREATED,
        source_image_ref=source_image_ref,
        parameters={},
    )


@pytest.fixture
def mock_project_repo():
    repo = Mock()
    repo.get.return_value = _make_project()
    return repo


@pytest.fixture
def mock_pattern_result_repo():
    return Mock()


@pytest.fixture
def mock_file_storage():
    storage = Mock()
    storage.read_source_image.return_value = b"\x89PNG fake image data"
    storage.save_pdf.return_value = "projects/proj-1/pattern.pdf"
    return storage


@pytest.fixture
def mock_image_resizer():
    resizer = Mock()

    def load_and_resize_side_effect(image_data, width, height, resampling="lanczos"):
        return [
            [(255 if (i + j) % 2 == 0 else 0, 0, 0) for j in range(width)]
            for i in range(height)
        ]

    resizer.load_and_resize.side_effect = load_and_resize_side_effect
    return resizer


@pytest.fixture
def mock_pdf_exporter():
    exporter = Mock()
    exporter.render.return_value = b"%PDF-1.4 fake pdf"
    return exporter


@pytest.fixture
def use_case(
    mock_project_repo,
    mock_pattern_result_repo,
    mock_file_storage,
    mock_image_resizer,
    mock_pdf_exporter,
):
    return CompleteExistingProject(
        project_repo=mock_project_repo,
        pattern_result_repo=mock_pattern_result_repo,
        file_storage=mock_file_storage,
        image_resizer=mock_image_resizer,
        pdf_exporter=mock_pdf_exporter,
    )


def _default_request(**overrides):
    defaults = dict(
        project_id="proj-1",
        num_colors=3,
        target_width=10,
        target_height=10,
    )
    defaults.update(overrides)
    return CompleteExistingProjectRequest(**defaults)


class TestCompleteExistingProjectNotFound:
    def test_raises_project_not_found_when_project_missing(self, use_case, mock_project_repo):
        mock_project_repo.get.return_value = None

        with pytest.raises(ProjectNotFoundError):
            use_case.execute(_default_request())

    def test_does_not_update_status_when_project_missing(self, use_case, mock_project_repo):
        mock_project_repo.get.return_value = None

        with pytest.raises(ProjectNotFoundError):
            use_case.execute(_default_request())

        mock_project_repo.update_status.assert_not_called()


class TestCompleteExistingProjectNoImage:
    def test_raises_domain_exception_when_no_source_image_ref(
        self, use_case, mock_project_repo
    ):
        mock_project_repo.get.return_value = _make_project(source_image_ref=None)

        with pytest.raises(DomainException):
            use_case.execute(_default_request())

    def test_does_not_update_status_when_no_source_image(
        self, use_case, mock_project_repo
    ):
        mock_project_repo.get.return_value = _make_project(source_image_ref=None)

        with pytest.raises(DomainException):
            use_case.execute(_default_request())

        mock_project_repo.update_status.assert_not_called()


class TestCompleteExistingProjectHappyPath:
    def test_reads_source_image_from_storage(self, use_case, mock_file_storage):
        use_case.execute(_default_request())

        mock_file_storage.read_source_image.assert_called_once_with(
            "proj-1", "projects/proj-1/source.png"
        )

    def test_status_transitions_to_in_progress_then_completed(
        self, use_case, mock_project_repo
    ):
        use_case.execute(_default_request())

        status_calls = mock_project_repo.update_status.call_args_list
        assert len(status_calls) == 2
        assert status_calls[0] == call("proj-1", ProjectStatus.IN_PROGRESS)
        assert status_calls[1] == call("proj-1", ProjectStatus.COMPLETED)

    def test_saves_pdf_to_storage(self, use_case, mock_file_storage):
        use_case.execute(_default_request())

        mock_file_storage.save_pdf.assert_called_once()
        call_args = mock_file_storage.save_pdf.call_args
        assert call_args[1]["data"] == b"%PDF-1.4 fake pdf"

    def test_saves_pattern_result(self, use_case, mock_pattern_result_repo):
        use_case.execute(_default_request())

        mock_pattern_result_repo.add.assert_called_once()
        saved = mock_pattern_result_repo.add.call_args[0][0]
        assert saved.project_id == "proj-1"
        assert saved.grid_width == 10
        assert saved.grid_height == 10
        assert saved.pdf_ref == "projects/proj-1/pattern.pdf"

    def test_returns_complete_result(self, use_case):
        result = use_case.execute(_default_request())

        assert isinstance(result, CompleteExistingProjectResult)
        assert result.project.id == "proj-1"
        assert result.pattern is not None
        assert len(result.dmc_colors) > 0
        assert result.pattern_result is not None
        assert result.pdf_bytes == b"%PDF-1.4 fake pdf"

    def test_result_project_has_completed_status(self, use_case):
        result = use_case.execute(_default_request())

        assert result.project.status == ProjectStatus.COMPLETED

    def test_calls_image_resizer_with_request_dimensions(
        self, use_case, mock_image_resizer
    ):
        use_case.execute(_default_request(target_width=20, target_height=15))

        # The resizer is called twice: once for the thumbnail (mode detection)
        # and once for the final resize with the requested dimensions.
        calls = mock_image_resizer.load_and_resize.call_args_list
        assert len(calls) == 2
        # The second call uses the requested target dimensions.
        final_call_args = calls[1][0]
        assert final_call_args[1] == 20
        assert final_call_args[2] == 15


class TestCompleteExistingProjectFailure:
    def test_sets_status_to_failed_when_processing_raises(
        self, use_case, mock_project_repo, mock_image_resizer
    ):
        mock_image_resizer.load_and_resize.side_effect = RuntimeError("GPU exploded")

        with pytest.raises(RuntimeError, match="GPU exploded"):
            use_case.execute(_default_request())

        status_calls = mock_project_repo.update_status.call_args_list
        # IN_PROGRESS first, then FAILED
        assert status_calls[0] == call("proj-1", ProjectStatus.IN_PROGRESS)
        assert status_calls[-1] == call("proj-1", ProjectStatus.FAILED)

    def test_reraises_exception_after_marking_failed(
        self, use_case, mock_pdf_exporter
    ):
        mock_pdf_exporter.render.side_effect = Exception("PDF broke")

        with pytest.raises(Exception, match="PDF broke"):
            use_case.execute(_default_request())
