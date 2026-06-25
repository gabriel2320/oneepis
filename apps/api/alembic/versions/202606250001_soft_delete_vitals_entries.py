"""soft delete vital signs and clinical entries

Revision ID: 202606250001
Revises: 202606200015
Create Date: 2026-06-25
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606250001"
down_revision = "202606200015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE clinical_entry_status ADD VALUE IF NOT EXISTS 'entered_in_error'")

    op.add_column(
        "vital_signs",
        sa.Column(
            "status",
            _record_status_type(),
            server_default="active",
            nullable=False,
        ),
    )
    if bind.dialect.name == "postgresql":
        op.alter_column("vital_signs", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("vital_signs", "status")


def _record_status_type():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.ENUM(
            "active",
            "inactive",
            "resolved",
            "entered_in_error",
            name="record_status",
            create_type=False,
        )
    return sa.Enum(
        "active",
        "inactive",
        "resolved",
        "entered_in_error",
        name="record_status",
    )
