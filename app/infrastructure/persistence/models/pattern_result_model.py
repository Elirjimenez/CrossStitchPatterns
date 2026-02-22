from sqlalchemy import JSON, String, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base

from datetime import datetime


class PatternResultModel(Base):
    __tablename__ = "pattern_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    palette: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    grid_width: Mapped[int] = mapped_column(Integer, nullable=False)
    grid_height: Mapped[int] = mapped_column(Integer, nullable=False)
    stitch_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pdf_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    variant: Mapped[str | None] = mapped_column(String(10), nullable=True)
    aida_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    margin_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
