"""
HTML Routes

Server-rendered page routes. These return full HTML responses via Jinja2 templates,
as opposed to the JSON API routes under /api.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Render the home page."""
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/projects", response_class=HTMLResponse)
async def projects(request: Request) -> HTMLResponse:
    """Render the projects placeholder page."""
    return templates.TemplateResponse("projects.html", {"request": request})
