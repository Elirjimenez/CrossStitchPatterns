"""Tests for FastAPI dependency injection functions."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.web.api import dependencies
from app.application.ports.file_storage import FileStorage
from app.infrastructure.storage.local_file_storage import LocalFileStorage


class TestGetSessionFactory:
    """Tests for _get_session_factory function."""

    def test_lazy_initialization(self):
        """Should initialize session factory on first call."""
        # Reset the global variable
        dependencies._session_factory = None

        with patch("app.web.api.dependencies.get_settings") as mock_settings:
            with patch("app.web.api.dependencies.build_session_factory") as mock_build:
                mock_settings.return_value.database_url = "sqlite:///:memory:"
                mock_factory = MagicMock()
                mock_build.return_value = mock_factory

                # First call should build the factory
                result = dependencies._get_session_factory()

                assert result == mock_factory
                mock_build.assert_called_once_with("sqlite:///:memory:")

    def test_returns_cached_factory_on_second_call(self):
        """Should return cached factory on subsequent calls."""
        # Set up a mock factory
        mock_factory = MagicMock()
        dependencies._session_factory = mock_factory

        with patch("app.web.api.dependencies.build_session_factory") as mock_build:
            # Second call should not build again
            result = dependencies._get_session_factory()

            assert result == mock_factory
            mock_build.assert_not_called()

        # Clean up
        dependencies._session_factory = None


class TestGetDbSession:
    """Tests for get_db_session dependency."""

    def test_yields_session_and_commits(self):
        """Should yield session and commit on success."""
        mock_factory = MagicMock()
        mock_session = MagicMock()
        mock_factory.return_value = mock_session

        with patch("app.web.api.dependencies._get_session_factory", return_value=mock_factory):
            # Use the generator
            generator = dependencies.get_db_session()
            session = next(generator)

            assert session == mock_session

            # Complete the generator (simulates successful endpoint execution)
            try:
                next(generator)
            except StopIteration:
                pass

            # Should commit and close
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_rolls_back_on_sqlalchemy_error(self):
        """Should rollback and close session on SQLAlchemyError."""
        mock_factory = MagicMock()
        mock_session = MagicMock()
        mock_factory.return_value = mock_session

        with patch("app.web.api.dependencies._get_session_factory", return_value=mock_factory):
            generator = dependencies.get_db_session()
            session = next(generator)

            # Simulate an error by throwing exception into generator
            with pytest.raises(SQLAlchemyError):
                generator.throw(SQLAlchemyError("Database error"))

            # Should rollback and close
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            # Should not commit
            mock_session.commit.assert_not_called()

    def test_closes_session_even_on_error(self):
        """Should always close session in finally block."""
        mock_factory = MagicMock()
        mock_session = MagicMock()
        mock_factory.return_value = mock_session

        with patch("app.web.api.dependencies._get_session_factory", return_value=mock_factory):
            generator = dependencies.get_db_session()
            next(generator)

            # Even with error, should close
            try:
                generator.throw(SQLAlchemyError("Error"))
            except SQLAlchemyError:
                pass

            mock_session.close.assert_called_once()


class TestGetFileStorage:
    """Tests for get_file_storage dependency."""

    def test_creates_file_storage_with_settings(self):
        """Should create LocalFileStorage with settings."""
        with patch("app.web.api.dependencies.get_settings") as mock_settings:
            mock_settings.return_value.storage_dir = "/test/storage"
            mock_settings.return_value.max_filename_length = 200
            mock_settings.return_value.allowed_file_extensions = ".png,.jpg"

            result = dependencies.get_file_storage()

            assert isinstance(result, LocalFileStorage)
            # Verify it was created with correct settings
            assert result._base_dir.name == "storage"  # Path object
            assert result._max_filename_length == 200
            assert result._allowed_extensions == {".png", ".jpg"}

    def test_parses_comma_separated_extensions(self):
        """Should correctly parse comma-separated extensions."""
        with patch("app.web.api.dependencies.get_settings") as mock_settings:
            mock_settings.return_value.storage_dir = "/test/storage"
            mock_settings.return_value.max_filename_length = 255
            mock_settings.return_value.allowed_file_extensions = ".pdf, .png , .jpg"

            result = dependencies.get_file_storage()

            # Should strip whitespace
            assert result._allowed_extensions == {".pdf", ".png", ".jpg"}

    def test_returns_file_storage_protocol(self):
        """Should return object implementing FileStorage protocol."""
        with patch("app.web.api.dependencies.get_settings") as mock_settings:
            mock_settings.return_value.storage_dir = "/test/storage"
            mock_settings.return_value.max_filename_length = 255
            mock_settings.return_value.allowed_file_extensions = ".png,.jpg,.pdf"

            result = dependencies.get_file_storage()

            # Should satisfy the FileStorage protocol
            assert isinstance(result, FileStorage)


class TestGetUseCaseDependencies:
    """Tests for use case dependency functions."""

    def test_get_calculate_fabric_use_case(self):
        """Should create CalculateFabricRequirements use case."""
        use_case = dependencies.get_calculate_fabric_use_case()
        assert use_case is not None

    def test_get_convert_image_use_case(self):
        """Should create ConvertImageToPattern use case."""
        with patch("app.web.api.dependencies.get_image_resizer") as mock_resizer:
            mock_resizer.return_value = MagicMock()
            use_case = dependencies.get_convert_image_use_case(mock_resizer.return_value)
            assert use_case is not None

    def test_get_export_pdf_use_case(self):
        """Should create ExportPatternToPdf use case."""
        with patch("app.web.api.dependencies.get_pdf_exporter") as mock_exporter:
            mock_exporter.return_value = MagicMock()
            use_case = dependencies.get_export_pdf_use_case(mock_exporter.return_value)
            assert use_case is not None
