"""add aida_count and margin_cm to pattern_results

Revision ID: d2f3a4b5c6e7
Revises: c1e2f3a4b5d6
Create Date: 2026-02-22

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2f3a4b5c6e7"
down_revision: Union[str, None] = "c1e2f3a4b5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pattern_results",
        sa.Column("aida_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "pattern_results",
        sa.Column("margin_cm", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pattern_results", "margin_cm")
    op.drop_column("pattern_results", "aida_count")
