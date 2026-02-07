"""
Health Check Endpoints

Provides health status and system information endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns basic health status and application version.
    Useful for monitoring and load balancer health checks.

    Returns:
        HealthResponse: Health status and version information
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
    )
