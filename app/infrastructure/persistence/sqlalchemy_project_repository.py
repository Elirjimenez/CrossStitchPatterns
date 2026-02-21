from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain.model.project import Project, ProjectStatus
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.persistence.mappers.project_mapper import ProjectMapper
from app.infrastructure.persistence.models.project_model import ProjectModel


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> None:
        model = ProjectMapper.to_model(project)
        self._session.add(model)
        self._session.flush()

    def get(self, project_id: str) -> Optional[Project]:
        model = self._session.get(ProjectModel, project_id)
        if model is None:
            return None
        return ProjectMapper.to_domain(model)

    def list_all(self) -> List[Project]:
        models = self._session.query(ProjectModel).order_by(ProjectModel.created_at.desc()).all()
        return [ProjectMapper.to_domain(m) for m in models]

    def update_status(self, project_id: str, status: ProjectStatus) -> None:
        model = self._session.get(ProjectModel, project_id)
        if model is None:
            return
        model.status = status.value
        self._session.flush()

    def update_source_image_ref(self, project_id: str, ref: str) -> None:
        model = self._session.get(ProjectModel, project_id)
        if model is None:
            return
        model.source_image_ref = ref
        self._session.flush()

    def update_source_image_metadata(
        self, project_id: str, *, ref: str, width: int, height: int
    ) -> None:
        model = self._session.get(ProjectModel, project_id)
        if model is None:
            return
        model.source_image_ref = ref
        model.source_image_width = width
        model.source_image_height = height
        self._session.flush()
