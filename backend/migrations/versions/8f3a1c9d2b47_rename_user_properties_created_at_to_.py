"""rename user_properties.created_at to associated_at

Revision ID: 8f3a1c9d2b47
Revises: 27e174f256c3
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '8f3a1c9d2b47'
down_revision: Union[str, Sequence[str], None] = '27e174f256c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("user_properties", "created_at", new_column_name="associated_at")


def downgrade() -> None:
    op.alter_column("user_properties", "associated_at", new_column_name="created_at")
