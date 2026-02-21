"""add source image dimensions to projects

Revision ID: b7e3f1a2c4d5
Revises: 4d14890bf062
Create Date: 2026-02-21 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e3f1a2c4d5"
down_revision: Union[str, None] = "4d14890bf062"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("source_image_width", sa.Integer, nullable=True))
    op.add_column("projects", sa.Column("source_image_height", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "source_image_height")
    op.drop_column("projects", "source_image_width")
