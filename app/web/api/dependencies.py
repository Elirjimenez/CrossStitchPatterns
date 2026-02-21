from typing import Generator

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.application.ports.file_storage import FileStorage
from app.application.ports.image_resizer import ImageResizer
from app.application.ports.pattern_pdf_exporter import PatternPdfExporter
from app.application.use_cases.calculate_fabric_requirements import (
    CalculateFabricRequirements,
)
from app.application.use_cases.convert_image_to_pattern import ConvertImageToPattern
from app.application.use_cases.complete_existing_project import CompleteExistingProject
from app.application.use_cases.create_complete_pattern import CreateCompletePattern
from app.application.use_cases.export_pattern_to_pdf import ExportPatternToPdf
from app.config import get_settings
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.image_processing.pillow_image_resizer import PillowImageResizer
from app.infrastructure.pdf_export.pattern_pdf_exporter import ReportLabPatternPdfExporter
from app.infrastructure.persistence.database import build_session_factory
from app.infrastructure.persistence.sqlalchemy_pattern_result_repository import (
    SqlAlchemyPatternResultRepository,
)
from app.infrastructure.persistence.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.storage.local_file_storage import LocalFileStorage

_session_factory = None


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        settings = get_settings()
        _session_factory = build_session_factory(settings.database_url)
    return _session_factory


def get_db_session() -> Generator[Session, None, None]:
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def get_file_storage() -> FileStorage:
    settings = get_settings()
    # Parse allowed extensions from comma-separated string
    allowed_extensions = {ext.strip() for ext in settings.allowed_file_extensions.split(",")}
    return LocalFileStorage(
        base_dir=settings.storage_dir,
        max_filename_length=settings.max_filename_length,
        allowed_extensions=allowed_extensions,
    )


def get_project_repository(
    session: Session = Depends(get_db_session),
) -> ProjectRepository:
    """Dependency for ProjectRepository."""
    return SqlAlchemyProjectRepository(session)


def get_pattern_result_repository(
    session: Session = Depends(get_db_session),
) -> PatternResultRepository:
    """Dependency for PatternResultRepository."""
    return SqlAlchemyPatternResultRepository(session)


def get_image_resizer() -> ImageResizer:
    """Dependency for ImageResizer."""
    return PillowImageResizer()


def get_pdf_exporter() -> PatternPdfExporter:
    """Dependency for PatternPdfExporter."""
    return ReportLabPatternPdfExporter()


def get_calculate_fabric_use_case() -> CalculateFabricRequirements:
    """Dependency for CalculateFabricRequirements use case."""
    return CalculateFabricRequirements()


def get_convert_image_use_case(
    image_resizer: ImageResizer = Depends(get_image_resizer),
) -> ConvertImageToPattern:
    """Dependency for ConvertImageToPattern use case."""
    return ConvertImageToPattern(image_resizer=image_resizer)


def get_export_pdf_use_case(
    pdf_exporter: PatternPdfExporter = Depends(get_pdf_exporter),
) -> ExportPatternToPdf:
    """Dependency for ExportPatternToPdf use case."""
    return ExportPatternToPdf(exporter=pdf_exporter)


def get_create_complete_pattern_use_case(
    project_repo: ProjectRepository = Depends(get_project_repository),
    pattern_result_repo: PatternResultRepository = Depends(get_pattern_result_repository),
    file_storage: FileStorage = Depends(get_file_storage),
    image_resizer: ImageResizer = Depends(get_image_resizer),
    pdf_exporter: PatternPdfExporter = Depends(get_pdf_exporter),
) -> CreateCompletePattern:
    """Dependency for CreateCompletePattern orchestrating use case."""
    return CreateCompletePattern(
        project_repo=project_repo,
        pattern_result_repo=pattern_result_repo,
        file_storage=file_storage,
        image_resizer=image_resizer,
        pdf_exporter=pdf_exporter,
    )


def get_complete_existing_project_use_case(
    project_repo: ProjectRepository = Depends(get_project_repository),
    pattern_result_repo: PatternResultRepository = Depends(get_pattern_result_repository),
    file_storage: FileStorage = Depends(get_file_storage),
    image_resizer: ImageResizer = Depends(get_image_resizer),
    pdf_exporter: PatternPdfExporter = Depends(get_pdf_exporter),
) -> CompleteExistingProject:
    """Dependency for CompleteExistingProject use case (generate pattern for existing project)."""
    return CompleteExistingProject(
        project_repo=project_repo,
        pattern_result_repo=pattern_result_repo,
        file_storage=file_storage,
        image_resizer=image_resizer,
        pdf_exporter=pdf_exporter,
    )
