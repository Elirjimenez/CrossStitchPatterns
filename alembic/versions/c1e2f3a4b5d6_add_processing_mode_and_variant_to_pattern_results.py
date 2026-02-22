"""add processing_mode and variant to pattern_results

Revision ID: c1e2f3a4b5d6
Revises: b7e3f1a2c4d5
Create Date: 2026-02-22

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1e2f3a4b5d6"
down_revision: Union[str, None] = "b7e3f1a2c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pattern_results",
        sa.Column("processing_mode", sa.String(20), nullable=True),
    )
    op.add_column(
        "pattern_results",
        sa.Column("variant", sa.String(10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pattern_results", "variant")
    op.drop_column("pattern_results", "processing_mode")
