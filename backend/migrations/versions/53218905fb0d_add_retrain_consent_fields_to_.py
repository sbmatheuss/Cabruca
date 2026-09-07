"""add retrain consent fields to properties

Revision ID: 53218905fb0d
Revises: 8f3a1c9d2b47
Create Date: 2026-09-06 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '53218905fb0d'
down_revision: str | Sequence[str] | None = '8f3a1c9d2b47'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("retrain_consent", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "properties",
        sa.Column("retrain_consent_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "properties",
        sa.Column(
            "retrain_consent_updated_by", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.create_foreign_key(
        "fk_properties_retrain_consent_updated_by_users",
        "properties",
        "users",
        ["retrain_consent_updated_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_properties_retrain_consent_updated_by_users", "properties", type_="foreignkey"
    )
    op.drop_column("properties", "retrain_consent_updated_by")
    op.drop_column("properties", "retrain_consent_updated_at")
    op.drop_column("properties", "retrain_consent")
