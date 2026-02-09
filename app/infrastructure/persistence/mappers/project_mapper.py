from app.domain.model.project import Project, ProjectStatus
from app.infrastructure.persistence.models.project_model import ProjectModel


class ProjectMapper:
    @staticmethod
    def to_model(domain: Project) -> ProjectModel:
        return ProjectModel(
            id=domain.id,
            name=domain.name,
            created_at=domain.created_at,
            status=domain.status.value,
            source_image_ref=domain.source_image_ref,
            parameters=domain.parameters,
        )

    @staticmethod
    def to_domain(model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
            status=ProjectStatus(model.status),
            source_image_ref=model.source_image_ref,
            parameters=model.parameters,
        )
