"""
Cross-Stitch Pattern Generator - Main Application

This module initializes the FastAPI application and configures routes.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.web.api.routes import health, patterns

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
APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Initialize database connection
    # TODO: Set up logging
    yield
    # TODO: Close database connections


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router, tags=["health"])
    app.include_router(patterns.router, prefix="/api/patterns", tags=["patterns"])

    return app


# Create application instance
app = create_app()
