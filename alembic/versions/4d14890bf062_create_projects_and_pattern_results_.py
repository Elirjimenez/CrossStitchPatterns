"""create projects and pattern_results tables

Revision ID: 4d14890bf062
Revises:
Create Date: 2026-02-09 22:05:18.802785

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4d14890bf062"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="created"),
        sa.Column("source_image_ref", sa.Text, nullable=True),
        sa.Column("parameters", postgresql.JSONB, nullable=False, server_default="{}"),
    )

    op.create_table(
        "pattern_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("palette", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("grid_width", sa.Integer, nullable=False),
        sa.Column("grid_height", sa.Integer, nullable=False),
        sa.Column("stitch_count", sa.Integer, nullable=False),
        sa.Column("pdf_ref", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("pattern_results")
    op.drop_table("projects")
