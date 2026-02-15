"""
Cross-Stitch Pattern Generator - Main Application

This module initializes the FastAPI application and configures routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.domain.exceptions import DomainException
from app.infrastructure.logging import setup_logging
from app.web.api.routes import health, patterns, projects

# Application metadata
APP_TITLE = "Cross-Stitch Pattern Generator"
APP_DESCRIPTION = """
Convert images into cross-stitch patterns with fabric and thread calculations.

## Features
* Calculate fabric requirements based on pattern dimensions
* Convert images to cross-stitch patterns
* Generate printable PDF patterns
* Store and retrieve patterns
"""


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = setup_logging()
    logger.info("application_startup")
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    # Parse allowed origins from settings (comma-separated string)
    origins = [origin.strip() for origin in settings.allowed_origins.split(",")]

    # Security: Only allow credentials with specific origins, not wildcards
    use_credentials = "*" not in origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=use_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    app.add_exception_handler(DomainException, domain_exception_handler)

    # Register routes
    app.include_router(health.router, tags=["health"])
    app.include_router(patterns.router, prefix="/api/patterns", tags=["patterns"])
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

    return app


# Create application instance
app = create_app()
