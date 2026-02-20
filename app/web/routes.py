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

from app.application.use_cases.list_projects import ListProjects
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
