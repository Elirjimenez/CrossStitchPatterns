import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.application.ports.file_storage import FileStorage
from app.application.use_cases.create_complete_pattern import (
    CreateCompletePattern,
    CreateCompletePatternRequest,
)
from app.application.use_cases.create_project import CreateProject, CreateProjectRequest
from app.application.use_cases.get_project import GetProject
from app.application.use_cases.list_projects import ListProjects
from app.application.use_cases.update_project_status import UpdateProjectStatus
from app.application.use_cases.save_pattern_result import (
    SavePatternResult,
    SavePatternResultRequest,
)
from app.config import Settings, get_settings
from app.domain.exceptions import DomainException, ProjectNotFoundError
from app.domain.model.project import ProjectStatus
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.web.api.dependencies import (
    get_create_complete_pattern_use_case,
    get_file_storage,
    get_pattern_result_repository,
    get_project_repository,
)
from app.web.validators import validate_generation_limits

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
def create_project(
    body: CreateProjectBody,
    repo: ProjectRepository = Depends(get_project_repository),
):
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
def list_projects(repo: ProjectRepository = Depends(get_project_repository)):
    use_case = ListProjects(project_repo=repo)
    projects = use_case.execute()
    return [_project_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository),
):
    use_case = GetProject(project_repo=repo)
    project = use_case.execute(project_id)
    return _project_to_response(project)


@router.patch("/{project_id}/status", status_code=204)
def update_project_status(
    project_id: str,
    body: UpdateStatusBody,
    repo: ProjectRepository = Depends(get_project_repository),
):
    use_case = UpdateProjectStatus(project_repo=repo)
    use_case.execute(project_id, ProjectStatus(body.status))


@router.post("/{project_id}/patterns", response_model=PatternResultResponse, status_code=201)
def create_pattern_result(
    project_id: str,
    body: CreatePatternResultBody,
    project_repo: ProjectRepository = Depends(get_project_repository),
    pattern_repo: PatternResultRepository = Depends(get_pattern_result_repository),
):
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


@router.post(
    "/{project_id}/source-image",
    response_model=ProjectResponse,
    status_code=200,
)
async def upload_source_image(
    project_id: str,
    file: UploadFile = File(...),
    repo: ProjectRepository = Depends(get_project_repository),
    storage: FileStorage = Depends(get_file_storage),
):
    project = repo.get(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    data = await file.read()
    _, extension = os.path.splitext(file.filename or "file.bin")
    ref = storage.save_source_image(project_id, data, extension)
    repo.update_source_image_ref(project_id, ref)

    updated = repo.get(project_id)
    return _project_to_response(updated)


@router.post(
    "/{project_id}/patterns/with-pdf",
    response_model=PatternResultResponse,
    status_code=201,
)
async def create_pattern_result_with_pdf(
    project_id: str,
    file: UploadFile = File(...),
    palette: str = Form(default="{}"),
    grid_width: int = Form(...),
    grid_height: int = Form(...),
    stitch_count: int = Form(...),
    project_repo: ProjectRepository = Depends(get_project_repository),
    pattern_repo: PatternResultRepository = Depends(get_pattern_result_repository),
    storage: FileStorage = Depends(get_file_storage),
):
    pdf_data = await file.read()
    pdf_ref = storage.save_pdf(project_id, pdf_data, "pattern.pdf")

    try:
        parsed_palette = json.loads(palette)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in palette field: {e}")

    use_case = SavePatternResult(project_repo=project_repo, pattern_result_repo=pattern_repo)
    result = use_case.execute(
        SavePatternResultRequest(
            project_id=project_id,
            palette=parsed_palette,
            grid_width=grid_width,
            grid_height=grid_height,
            stitch_count=stitch_count,
            pdf_ref=pdf_ref,
        )
    )
    return _pattern_result_to_response(result)


# --- POST /api/projects/complete ---


class CompletePatternResponse(BaseModel):
    """Response for the complete pattern creation workflow."""

    project: ProjectResponse
    pattern_result: PatternResultResponse
    pdf_url: str  # In a real app, this would be a download URL


@router.post("/complete", response_model=CompletePatternResponse, status_code=201)
async def create_complete_pattern(
    name: str = Form(..., min_length=1),
    file: UploadFile = File(...),
    num_colors: int = Form(..., gt=0),
    target_width: Optional[int] = Form(default=None, gt=0),
    target_height: Optional[int] = Form(default=None, gt=0),
    min_frequency_pct: float = Form(default=1.0, ge=0.0, le=100.0),
    aida_count: int = Form(default=14, gt=0),
    num_strands: int = Form(default=2, ge=1, le=6),
    margin_cm: float = Form(default=5.0, ge=0),
    variant: str = Form(default="color", pattern="^(color|bw)$"),
    use_case: CreateCompletePattern = Depends(get_create_complete_pattern_use_case),
    settings: Settings = Depends(get_settings),
):
    """
    Complete end-to-end workflow: create project, upload image, generate pattern,
    export PDF, save all results, and mark project as completed.

    If target_width and target_height are not provided, the pattern will use
    the actual dimensions of the uploaded image.

    All operations are performed in a single transaction.
    If any step fails, the entire operation is rolled back.
    """
    try:
        validate_generation_limits(
            num_colors=num_colors,
            target_w=target_width,
            target_h=target_height,
            settings=settings,
        )
    except DomainException as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    image_data = await file.read()

    request = CreateCompletePatternRequest(
        name=name,
        image_data=image_data,
        image_filename=file.filename or "image.bin",
        target_width=target_width,
        target_height=target_height,
        num_colors=num_colors,
        min_frequency_pct=min_frequency_pct,
        aida_count=aida_count,
        num_strands=num_strands,
        margin_cm=margin_cm,
        variant=variant,
    )

    result = use_case.execute(request)

    return CompletePatternResponse(
        project=_project_to_response(result.project),
        pattern_result=_pattern_result_to_response(result.pattern_result),
        pdf_url=f"/api/projects/files/{result.pattern_result.pdf_ref}",
    )


# --- GET /api/projects/files/{file_path:path} ---


@router.get("/files/{file_path:path}")
def download_file(
    file_path: str,
    storage: FileStorage = Depends(get_file_storage),
):
    """
    Download a file from project storage (source images, PDFs, etc.).

    The file_path should be the relative path returned from other endpoints,
    e.g., "projects/{project_id}/pattern.pdf"

    Security: Path traversal attempts will return 404.
    """
    # Use secure resolution method with path traversal protection
    absolute_path = storage.resolve_file_for_download(file_path)

    if absolute_path is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type based on extension
    extension = file_path.lower().split(".")[-1]
    media_type_map = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    media_type = media_type_map.get(extension, "application/octet-stream")

    # Get filename for download
    filename = file_path.split("/")[-1]

    return FileResponse(
        path=str(absolute_path),
        media_type=media_type,
        filename=filename,
    )
