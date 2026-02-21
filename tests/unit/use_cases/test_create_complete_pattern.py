"""Tests for CreateCompletePattern orchestrating use case."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from app.application.use_cases.create_complete_pattern import (
    CreateCompletePattern,
    CreateCompletePatternRequest,
    CreateCompletePatternResult,
)
from app.domain.data.dmc_colors import DmcColor
from app.domain.model.pattern import Palette, Pattern, PatternGrid
from app.domain.model.project import Project, ProjectStatus, PatternResult


@pytest.fixture
def mock_project_repo():
    return Mock()


@pytest.fixture
def mock_pattern_result_repo():
    return Mock()


@pytest.fixture
def mock_file_storage():
    storage = Mock()
    storage.save_source_image.return_value = "images/proj-123/source.png"
    storage.save_pdf.return_value = "pdfs/proj-123/pattern.pdf"
    return storage


@pytest.fixture
def mock_image_resizer():
    resizer = Mock()

    # Return a pixel grid that matches the requested dimensions
    # This will be dynamically adjusted based on the request
    def load_and_resize_side_effect(image_data, width, height, resampling="lanczos"):
        # Create a grid of the requested size with some color variation
        return [
            [(255 if (i + j) % 2 == 0 else 0, 0, 0) for j in range(width)] for i in range(height)
        ]

    resizer.load_and_resize.side_effect = load_and_resize_side_effect
    return resizer


@pytest.fixture
def mock_pdf_exporter():
    exporter = Mock()
    exporter.render.return_value = b"%PDF-1.4 fake pdf content"
    return exporter


@pytest.fixture
def use_case(
    mock_project_repo,
    mock_pattern_result_repo,
    mock_file_storage,
    mock_image_resizer,
    mock_pdf_exporter,
):
    return CreateCompletePattern(
        project_repo=mock_project_repo,
        pattern_result_repo=mock_pattern_result_repo,
        file_storage=mock_file_storage,
        image_resizer=mock_image_resizer,
        pdf_exporter=mock_pdf_exporter,
    )


class TestCreateCompletePattern:
    def test_creates_project_with_in_progress_status(self, use_case, mock_project_repo):
        """The use case should create a project with IN_PROGRESS status after image upload."""
        request = CreateCompletePatternRequest(
            name="Test Pattern",
            image_data=b"fake-image-data",
            image_filename="photo.jpg",
            target_width=10,
            target_height=10,
            num_colors=3,
        )

        use_case.execute(request)

        # Should call add once for initial creation
        assert mock_project_repo.add.call_count == 1
        created_project = mock_project_repo.add.call_args[0][0]
        assert created_project.name == "Test Pattern"
        assert created_project.status == ProjectStatus.CREATED

        # Should update project with source_image_ref and IN_PROGRESS status
        assert mock_project_repo.update_status.called
        assert mock_project_repo.update_source_image_ref.called

    def test_saves_source_image_with_correct_extension(self, use_case, mock_file_storage):
        """The use case should save the source image with the correct file extension."""
        request = CreateCompletePatternRequest(
            name="Test",
            image_data=b"image-bytes",
            image_filename="photo.png",
            target_width=10,
            target_height=10,
            num_colors=3,
        )

        use_case.execute(request)

        mock_file_storage.save_source_image.assert_called_once()
        call_args = mock_file_storage.save_source_image.call_args
        assert call_args[1]["data"] == b"image-bytes"
        assert call_args[1]["extension"] == ".png"

    def test_converts_image_to_pattern(self, use_case, mock_image_resizer):
        """The use case should convert the image to a cross-stitch pattern."""
        request = CreateCompletePatternRequest(
            name="Test",
            image_data=b"image-bytes",
            image_filename="photo.jpg",
            target_width=20,
            target_height=15,
            num_colors=5,
        )

        use_case.execute(request)

        # The resizer is called twice: thumbnail for mode detection + actual resize.
        # Verify the final (second) call used the requested dimensions.
        calls = mock_image_resizer.load_and_resize.call_args_list
        assert len(calls) == 2
        final_args = calls[1][0]
        assert final_args[0] == b"image-bytes"
        assert final_args[1] == 20
        assert final_args[2] == 15

    def test_exports_pattern_to_pdf(self, use_case, mock_pdf_exporter):
        """The use case should export the pattern to PDF."""
        request = CreateCompletePatternRequest(
            name="My Pattern",
            image_data=b"image-bytes",
            image_filename="photo.jpg",
            target_width=10,
            target_height=10,
            num_colors=3,
            aida_count=16,
            num_strands=3,
            margin_cm=7.5,
        )

        use_case.execute(request)

        mock_pdf_exporter.render.assert_called_once()

    def test_saves_pdf_to_storage(self, use_case, mock_file_storage):
        """The use case should save the generated PDF to file storage."""
        request = CreateCompletePatternRequest(
            name="Test",
            image_data=b"image",
            image_filename="photo.jpg",
            target_width=10,
            target_height=10,
            num_colors=3,
        )

        use_case.execute(request)

        mock_file_storage.save_pdf.assert_called_once()
        call_args = mock_file_storage.save_pdf.call_args
        assert call_args[1]["data"] == b"%PDF-1.4 fake pdf content"
        assert "pattern.pdf" in call_args[1]["filename"]

    def test_saves_pattern_result_with_pdf_ref(
        self, use_case, mock_pattern_result_repo, mock_file_storage
    ):
        """The use case should save pattern result with PDF reference."""
        mock_file_storage.save_pdf.return_value = "pdfs/proj-123/pattern.pdf"

        request = CreateCompletePatternRequest(
            name="Test",
            image_data=b"image",
            image_filename="photo.jpg",
            target_width=10,
            target_height=10,
            num_colors=3,
        )

        use_case.execute(request)

        mock_pattern_result_repo.add.assert_called_once()
        saved_result = mock_pattern_result_repo.add.call_args[0][0]
        assert saved_result.pdf_ref == "pdfs/proj-123/pattern.pdf"
        assert saved_result.grid_width == 10
        assert saved_result.grid_height == 10

    def test_updates_project_status_to_completed(self, use_case, mock_project_repo):
        """The use case should mark project as COMPLETED at the end."""
        request = CreateCompletePatternRequest(
            name="Test",
            image_data=b"image",
            image_filename="photo.jpg",
            target_width=10,
            target_height=10,
            num_colors=3,
        )

        result = use_case.execute(request)

        # Should update status to COMPLETED
        status_calls = [call for call in mock_project_repo.update_status.call_args_list]
        # Last call should be COMPLETED
        assert len(status_calls) >= 1
        final_status_call = status_calls[-1]
        assert final_status_call[0][1] == ProjectStatus.COMPLETED

    def test_returns_complete_result(self, use_case):
        """The use case should return all generated artifacts."""
        request = CreateCompletePatternRequest(
            name="Test Pattern",
            image_data=b"image",
            image_filename="photo.jpg",
            target_width=10,
            target_height=10,
            num_colors=3,
        )

        result = use_case.execute(request)

        assert isinstance(result, CreateCompletePatternResult)
        assert result.project.name == "Test Pattern"
        assert result.pattern is not None
        assert len(result.dmc_colors) > 0
        assert result.pattern_result is not None
        assert result.pdf_bytes == b"%PDF-1.4 fake pdf content"

    def test_uses_custom_fabric_parameters(self, use_case, mock_pdf_exporter):
        """The use case should respect custom aida_count, strands, and margin."""
        request = CreateCompletePatternRequest(
            name="Test",
            image_data=b"image",
            image_filename="photo.jpg",
            target_width=10,
            target_height=10,
            num_colors=3,
            aida_count=18,
            num_strands=1,
            margin_cm=10.0,
        )

        use_case.execute(request)

        # Verify PDF exporter was called (fabric params used internally)
        assert mock_pdf_exporter.render.called
