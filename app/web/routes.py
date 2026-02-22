"""
HTML Routes

Server-rendered page routes. These return full HTML responses via Jinja2 templates,
as opposed to the JSON API routes under /api.
"""

import io
import os
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.application.ports.file_storage import FileStorage
from app.application.use_cases.complete_existing_project import (
    CompleteExistingProject,
    CompleteExistingProjectRequest,
)
from app.application.use_cases.create_project import CreateProject, CreateProjectRequest
from app.application.use_cases.get_project import GetProject
from app.application.use_cases.list_projects import ListProjects
from app.config import Settings, get_settings
from app.domain.exceptions import DomainException, ProjectNotFoundError
from app.domain.model.project import ProjectStatus
from app.domain.repositories.pattern_result_repository import PatternResultRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.web.api.dependencies import (
    get_complete_existing_project_use_case,
    get_file_storage,
    get_pattern_result_repository,
    get_project_repository,
)
from app.web.validators import validate_generation_limits

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
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render the project detail page."""
    try:
        use_case = GetProject(project_repo=repo)
        project = use_case.execute(project_id)
        w = project.source_image_width
        h = project.source_image_height
        default_target_width = min(w, settings.max_target_width) if w else min(300, settings.max_target_width)
        default_target_height = min(h, settings.max_target_height) if h else min(300, settings.max_target_height)
        # Cap pixel product if it exceeds the pixel limit (scale proportionally)
        if default_target_width * default_target_height > settings.max_target_pixels:
            import math
            ratio = math.sqrt(settings.max_target_pixels / (default_target_width * default_target_height))
            default_target_width = max(10, int(default_target_width * ratio))
            default_target_height = max(10, int(default_target_height * ratio))
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
                "default_target_width": default_target_width,
                "default_target_height": default_target_height,
                "max_colors": settings.max_colors,
                "max_target_width": settings.max_target_width,
                "max_target_height": settings.max_target_height,
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

        # --- Extract image dimensions (rejects corrupt/non-image data) ---
        try:
            with Image.open(io.BytesIO(data)) as img:
                img_width, img_height = img.size
        except (UnidentifiedImageError, Exception):
            return _source_image_card(
                request, project_id, project.source_image_ref,
                error="The uploaded file could not be read as an image.",
                status_code=400,
            )

        _, extension = os.path.splitext(file.filename)
        ref = storage.save_source_image(project_id, data, extension)
        repo.update_source_image_metadata(project_id, ref=ref, width=img_width, height=img_height)

        response = _source_image_card(request, project_id, ref)
        response.headers["HX-Trigger"] = "actions:refresh"
        return response

    except Exception as exc:
        logger.error("hx_upload_source_image_failed", project_id=project_id, error=str(exc), exc_info=True)
        return _source_image_card(
            request, project_id, None,
            error="An unexpected error occurred. Please try again.",
            status_code=500,
        )


def _actions_context(project, settings: Settings) -> dict:
    """Compute the template context for the project_actions partial."""
    w = project.source_image_width
    h = project.source_image_height
    default_target_width = min(w, settings.max_target_width) if w else min(300, settings.max_target_width)
    default_target_height = min(h, settings.max_target_height) if h else min(300, settings.max_target_height)
    return {
        "project_id": project.id,
        "source_image_ref": project.source_image_ref,
        "default_target_width": default_target_width,
        "default_target_height": default_target_height,
    }


@router.get("/hx/projects/{project_id}/actions", response_class=HTMLResponse)
async def hx_project_actions(
    project_id: str,
    request: Request,
    repo: ProjectRepository = Depends(get_project_repository),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """
    HTMX partial endpoint: render the Actions panel for a project.

    Fetches fresh project state so that source_image_ref and image dimensions
    are always up-to-date. Called on initial page load and whenever the
    'actions:refresh' event fires (e.g. after a successful image upload).
    """
    project = repo.get(project_id)
    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/flash.html",
            {"success": False, "message": f"Project '{project_id}' not found."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/project_actions.html",
        _actions_context(project, settings),
    )


def _pattern_results_card(
    request: Request,
    project_id: str,
    *,
    success: bool | None = None,
    result: dict | None = None,
    pdf_url: str | None = None,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """Helper: render the pattern-results-card partial."""
    return templates.TemplateResponse(
        request,
        "partials/pattern_results_card.html",
        {
            "project_id": project_id,
            "success": success,
            "result": result,
            "pdf_url": pdf_url,
            "error": error,
        },
        status_code=status_code,
    )


@router.post("/hx/projects/{project_id}/generate", response_class=HTMLResponse)
async def hx_generate_pattern(
    project_id: str,
    request: Request,
    num_colors: int = Form(default=10),
    target_width: int = Form(default=300),
    target_height: int = Form(default=300),
    processing_mode: str = Form(default="auto"),
    use_case: CompleteExistingProject = Depends(get_complete_existing_project_use_case),
    repo: ProjectRepository = Depends(get_project_repository),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """
    HTMX partial endpoint: generate a cross-stitch pattern + PDF for an existing project.

    Validates numeric parameters and project state before calling the use case,
    then returns the pattern-results-card partial (HTMX outerHTML swap).
    """
    # --- Validate numeric parameters against configured safety limits ---
    try:
        validate_generation_limits(
            num_colors=num_colors,
            target_w=target_width,
            target_h=target_height,
            settings=settings,
        )
    except DomainException as exc:
        return _pattern_results_card(
            request, project_id,
            success=False,
            error=str(exc),
            status_code=400,
        )

    # --- Pre-flight: verify project exists and has a source image ---
    try:
        project = repo.get(project_id)
    except Exception as exc:
        logger.error("hx_generate_pattern_repo_failed", project_id=project_id, error=str(exc), exc_info=True)
        return _pattern_results_card(
            request, project_id,
            success=False,
            error="An unexpected error occurred. Please try again.",
            status_code=500,
        )

    if project is None:
        return _pattern_results_card(
            request, project_id,
            success=False,
            error=f"Project '{project_id}' not found.",
            status_code=404,
        )
    if not project.source_image_ref:
        return _pattern_results_card(
            request, project_id,
            success=False,
            error="Please upload a source image before generating a pattern.",
            status_code=400,
        )

    # --- Run the use case ---
    try:
        result = use_case.execute(
            CompleteExistingProjectRequest(
                project_id=project_id,
                num_colors=num_colors,
                target_width=target_width,
                target_height=target_height,
                processing_mode=processing_mode,
            )
        )
        pr = result.pattern_result
        num_palette_colors = len(pr.palette.get("colors", []))
        pdf_url = f"/api/projects/files/{pr.pdf_ref}" if pr.pdf_ref else None

        return _pattern_results_card(
            request,
            project_id,
            success=True,
            result={
                "grid_width": pr.grid_width,
                "grid_height": pr.grid_height,
                "stitch_count": pr.stitch_count,
                "num_colors": num_palette_colors,
                "created_at": pr.created_at.strftime("%d %b %Y %H:%M"),
            },
            pdf_url=pdf_url,
        )

    except DomainException as exc:
        return _pattern_results_card(
            request, project_id,
            success=False,
            error=str(exc),
            status_code=400,
        )

    except Exception as exc:
        logger.error("hx_generate_pattern_failed", project_id=project_id, error=str(exc), exc_info=True)
        return _pattern_results_card(
            request, project_id,
            success=False,
            error="An unexpected error occurred. Please try again.",
            status_code=500,
        )


@router.delete("/hx/projects/{project_id}", response_class=HTMLResponse)
async def hx_delete_project(
    project_id: str,
    request: Request,
    project_repo: ProjectRepository = Depends(get_project_repository),
    pattern_result_repo: PatternResultRepository = Depends(get_pattern_result_repository),
    storage: FileStorage = Depends(get_file_storage),
) -> HTMLResponse:
    """
    HTMX endpoint: permanently delete a project and all its data.

    Returns HX-Redirect to /projects on success so HTMX navigates back
    to the project list.
    """
    project = project_repo.get(project_id)

    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/flash.html",
            {"success": False, "message": f"Project '{project_id}' not found."},
            status_code=404,
        )

    if project.status == ProjectStatus.IN_PROGRESS:
        return templates.TemplateResponse(
            request,
            "partials/flash.html",
            {
                "success": False,
                "message": "Cannot delete a project while it is being processed.",
            },
            status_code=409,
        )

    # Delete DB records (pattern results first, then project)
    pattern_result_repo.delete_by_project(project_id)
    project_repo.delete(project_id)

    # Remove storage folder (best-effort — warn but don't fail)
    try:
        storage.delete_project_folder(project_id)
    except Exception as exc:
        logger.warning("delete_project_folder_failed", project_id=project_id, error=str(exc))

    response = HTMLResponse("", status_code=200)
    response.headers["HX-Redirect"] = "/projects"
    return response
