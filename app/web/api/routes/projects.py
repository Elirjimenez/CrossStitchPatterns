from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.use_cases.create_project import CreateProject, CreateProjectRequest
from app.application.use_cases.get_project import GetProject
from app.application.use_cases.list_projects import ListProjects
from app.application.use_cases.update_project_status import UpdateProjectStatus
from app.application.use_cases.save_pattern_result import (
    SavePatternResult,
    SavePatternResultRequest,
)
from app.domain.model.project import ProjectStatus
from app.infrastructure.persistence.sqlalchemy_project_repository import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.persistence.sqlalchemy_pattern_result_repository import (
    SqlAlchemyPatternResultRepository,
)
from app.web.api.dependencies import get_db_session

router = APIRouter()


# --- Schemas ---


class CreateProjectBody(BaseModel):
    name: str = Field(min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    source_image_ref: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: str
    status: str
    source_image_ref: Optional[str]
    parameters: Dict[str, Any]


class UpdateStatusBody(BaseModel):
    status: str = Field(pattern="^(created|in_progress|completed|failed)$")


class CreatePatternResultBody(BaseModel):
    palette: Dict[str, Any] = Field(default_factory=dict)
    grid_width: int = Field(gt=0)
    grid_height: int = Field(gt=0)
    stitch_count: int = Field(ge=0)
    pdf_ref: Optional[str] = None


class PatternResultResponse(BaseModel):
    id: str
    project_id: str
    created_at: str
    palette: Dict[str, Any]
    grid_width: int
    grid_height: int
    stitch_count: int
    pdf_ref: Optional[str]


# --- Helpers ---


def _project_to_response(project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        created_at=project.created_at.isoformat(),
        status=project.status.value,
        source_image_ref=project.source_image_ref,
        parameters=project.parameters,
    )


def _pattern_result_to_response(pr) -> PatternResultResponse:
    return PatternResultResponse(
        id=pr.id,
        project_id=pr.project_id,
        created_at=pr.created_at.isoformat(),
        palette=pr.palette,
        grid_width=pr.grid_width,
        grid_height=pr.grid_height,
        stitch_count=pr.stitch_count,
        pdf_ref=pr.pdf_ref,
    )


# --- Endpoints ---


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: CreateProjectBody, session: Session = Depends(get_db_session)):
    repo = SqlAlchemyProjectRepository(session)
    use_case = CreateProject(project_repo=repo)
    project = use_case.execute(
        CreateProjectRequest(
            name=body.name,
            parameters=body.parameters,
            source_image_ref=body.source_image_ref,
        )
    )
    return _project_to_response(project)


@router.get("", response_model=List[ProjectResponse])
def list_projects(session: Session = Depends(get_db_session)):
    repo = SqlAlchemyProjectRepository(session)
    use_case = ListProjects(project_repo=repo)
    projects = use_case.execute()
    return [_project_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, session: Session = Depends(get_db_session)):
    repo = SqlAlchemyProjectRepository(session)
    use_case = GetProject(project_repo=repo)
    project = use_case.execute(project_id)
    return _project_to_response(project)


@router.patch("/{project_id}/status", status_code=204)
def update_project_status(
    project_id: str,
    body: UpdateStatusBody,
    session: Session = Depends(get_db_session),
):
    repo = SqlAlchemyProjectRepository(session)
    use_case = UpdateProjectStatus(project_repo=repo)
    use_case.execute(project_id, ProjectStatus(body.status))


@router.post("/{project_id}/patterns", response_model=PatternResultResponse, status_code=201)
def create_pattern_result(
    project_id: str,
    body: CreatePatternResultBody,
    session: Session = Depends(get_db_session),
):
    project_repo = SqlAlchemyProjectRepository(session)
    pattern_repo = SqlAlchemyPatternResultRepository(session)
    use_case = SavePatternResult(project_repo=project_repo, pattern_result_repo=pattern_repo)
    result = use_case.execute(
        SavePatternResultRequest(
            project_id=project_id,
            palette=body.palette,
            grid_width=body.grid_width,
            grid_height=body.grid_height,
            stitch_count=body.stitch_count,
            pdf_ref=body.pdf_ref,
        )
    )
    return _pattern_result_to_response(result)
