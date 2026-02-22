from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from app.domain.exceptions import DomainException


class ProjectStatus(enum.Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    created_at: datetime
    status: ProjectStatus
    source_image_ref: Optional[str]
    parameters: Dict[str, Any]
    source_image_width: Optional[int] = None
    source_image_height: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainException("name must not be empty or blank")


@dataclass(frozen=True)
class PatternResult:
    id: str
    project_id: str
    created_at: datetime
    palette: Dict[str, Any]
    grid_width: int
    grid_height: int
    stitch_count: int
    pdf_ref: Optional[str]
    processing_mode: str = "auto"   # "auto" | "photo" | "drawing" | "pixel_art"
    variant: str = "color"          # "color" | "bw"
    aida_count: int = 14
    margin_cm: float = 5.0

    def __post_init__(self) -> None:
        if self.grid_width <= 0:
            raise DomainException("grid_width must be positive")
        if self.grid_height <= 0:
            raise DomainException("grid_height must be positive")
        if self.stitch_count < 0:
            raise DomainException("stitch_count must not be negative")
