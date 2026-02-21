from sqlalchemy import JSON, Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base

from datetime import datetime


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    source_image_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_image_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_image_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
