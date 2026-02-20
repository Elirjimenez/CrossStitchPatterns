"""
HTML Routes

Server-rendered page routes. These return full HTML responses via Jinja2 templates,
as opposed to the JSON API routes under /api.
"""

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fastapi import Form

from app.application.use_cases.create_project import CreateProject, CreateProjectRequest
from app.application.use_cases.get_project import GetProject
from app.application.use_cases.list_projects import ListProjects
from app.domain.exceptions import DomainException, ProjectNotFoundError
from app.domain.repositories.project_repository import ProjectRepository
from app.web.api.dependencies import get_project_repository

router = APIRouter()
logger = structlog.get_logger(__name__)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


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
