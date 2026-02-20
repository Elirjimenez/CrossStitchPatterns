"""
HTML Routes

Server-rendered page routes. These return full HTML responses via Jinja2 templates,
as opposed to the JSON API routes under /api.
"""

import os
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.application.ports.file_storage import FileStorage
from app.application.use_cases.create_project import CreateProject, CreateProjectRequest
from app.application.use_cases.get_project import GetProject
from app.application.use_cases.list_projects import ListProjects
from app.domain.exceptions import DomainException, ProjectNotFoundError
from app.domain.repositories.project_repository import ProjectRepository
from app.web.api.dependencies import get_file_storage, get_project_repository

router = APIRouter()
logger = structlog.get_logger(__name__)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Render the home page."""
    return templates.TemplateResponse(request, "home.html")


@router.get("/projects", response_class=HTMLResponse)
async def projects(request: Request) -> HTMLResponse:
    """Render the projects page. Content is loaded dynamically via HTMX."""
    return templates.TemplateResponse(request, "projects.html")


@router.get("/hx/projects", response_class=HTMLResponse)
async def hx_projects(
    request: Request,
    repo: ProjectRepository = Depends(get_project_repository),
) -> HTMLResponse:
    """
    HTMX partial endpoint: returns the projects list fragment.

    Called by hx-get on the projects page. Fetches projects via the same
    use case as the JSON API, avoiding an internal HTTP round-trip.
    """
    try:
        use_case = ListProjects(project_repo=repo)
        raw_projects = use_case.execute()
        project_list = [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status.value,
                "created_at": p.created_at.strftime("%d %b %Y"),
            }
            for p in raw_projects
        ]
        return templates.TemplateResponse(
            request,
            "partials/projects_list.html",
            {"projects": project_list, "error": False},
        )
    except Exception as exc:
        logger.error("hx_projects_failed", error=str(exc), exc_info=True)
        return templates.TemplateResponse(
            request,
            "partials/projects_list.html",
            {"projects": [], "error": True},
        )


@router.post("/hx/projects/create", response_class=HTMLResponse)
async def hx_create_project(
    request: Request,
    name: str = Form(default=""),
    repo: ProjectRepository = Depends(get_project_repository),
) -> HTMLResponse:
    """
    HTMX partial endpoint: creates a project and returns a flash message.

    On success, sets HX-Trigger: projectsChanged so the projects list reloads.
    """
    stripped_name = name.strip()

    if not stripped_name:
        return templates.TemplateResponse(
            request,
            "partials/flash.html",
            {"success": False, "message": "Project name is required."},
            status_code=400,
        )

    try:
        use_case = CreateProject(project_repo=repo)
        use_case.execute(CreateProjectRequest(name=stripped_name))
        response = templates.TemplateResponse(
            request,
            "partials/flash.html",
            {"success": True, "message": f'Project "{stripped_name}" created successfully.'},
        )
        response.headers["HX-Trigger"] = '{"projectsChanged": true}'
        return response

    except DomainException as exc:
        return templates.TemplateResponse(
            request,
            "partials/flash.html",
            {"success": False, "message": str(exc)},
            status_code=400,
        )

    except Exception as exc:
        logger.error("hx_create_project_failed", error=str(exc), exc_info=True)
        return templates.TemplateResponse(
            request,
            "partials/flash.html",
            {"success": False, "message": "An unexpected error occurred. Please try again."},
            status_code=500,
        )


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(
    project_id: str,
    request: Request,
    repo: ProjectRepository = Depends(get_project_repository),
) -> HTMLResponse:
    """Render the project detail page."""
    try:
        use_case = GetProject(project_repo=repo)
        project = use_case.execute(project_id)
        return templates.TemplateResponse(
            request,
            "project_detail.html",
            {
                "id": project.id,
                "name": project.name,
                "status": project.status.value,
                "created_at": project.created_at.strftime("%d %b %Y"),
                "source_image_ref": project.source_image_ref,
                "project_id": project.id,
            },
        )
    except ProjectNotFoundError:
        return templates.TemplateResponse(
            request,
            "project_not_found.html",
            {"project_id": project_id},
            status_code=404,
        )
    except Exception as exc:
        logger.error("project_detail_failed", project_id=project_id, error=str(exc), exc_info=True)
        return templates.TemplateResponse(
            request,
            "project_not_found.html",
            {"project_id": project_id, "unexpected_error": True},
            status_code=500,
        )


def _source_image_card(
    request: Request,
    project_id: str,
    source_image_ref: str | None,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """Helper: render the source image card partial."""
    return templates.TemplateResponse(
        request,
        "partials/source_image_card.html",
        {"project_id": project_id, "source_image_ref": source_image_ref, "error": error},
        status_code=status_code,
    )


@router.post("/hx/projects/{project_id}/source-image", response_class=HTMLResponse)
async def hx_upload_source_image(
    project_id: str,
    request: Request,
    file: UploadFile = File(...),
    repo: ProjectRepository = Depends(get_project_repository),
    storage: FileStorage = Depends(get_file_storage),
) -> HTMLResponse:
    """
    HTMX partial endpoint: upload a source image for a project.

    Validates file type, saves via FileStorage, updates the project ref,
    and returns the refreshed source-image card partial.
    """
    # --- Validate file presence ---
    if not file.filename:
        return _source_image_card(
            request, project_id, None,
            error="Please select an image file to upload.",
            status_code=400,
        )

    # --- Validate content type ---
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in _ALLOWED_IMAGE_TYPES:
        return _source_image_card(
            request, project_id, None,
            error="Only image files are accepted (PNG, JPEG, WebP, GIF).",
            status_code=400,
        )

    try:
        # --- Validate project exists ---
        project = repo.get(project_id)
        if project is None:
            return _source_image_card(
                request, project_id, None,
                error=f"Project '{project_id}' not found.",
                status_code=404,
            )

        # --- Read, validate size, and save ---
        data = await file.read()
        if len(data) > _MAX_UPLOAD_BYTES:
            return _source_image_card(
                request, project_id, project.source_image_ref,
                error="File is too large. Maximum size is 10 MB.",
                status_code=400,
            )

        _, extension = os.path.splitext(file.filename)
        ref = storage.save_source_image(project_id, data, extension)
        repo.update_source_image_ref(project_id, ref)

        return _source_image_card(request, project_id, ref)

    except Exception as exc:
        logger.error("hx_upload_source_image_failed", project_id=project_id, error=str(exc), exc_info=True)
        return _source_image_card(
            request, project_id, None,
            error="An unexpected error occurred. Please try again.",
            status_code=500,
        )
