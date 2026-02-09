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

    def __post_init__(self) -> None:
        if self.grid_width <= 0:
            raise DomainException("grid_width must be positive")
        if self.grid_height <= 0:
            raise DomainException("grid_height must be positive")
        if self.stitch_count < 0:
            raise DomainException("stitch_count must not be negative")
