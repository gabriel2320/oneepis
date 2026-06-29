"""vital sign status

Revision ID: 202606200021
Revises: 202606200020
Create Date: 2026-06-29
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200021"
down_revision = "202606200020"
branch_labels = None
depends_on = None

record_status = postgresql.ENUM(
    "active",
    "inactive",
    "resolved",
    "entered_in_error",
    name="record_status",
    create_type=False,
)


def upgrade() -> None:
    op.add_column(
        "vital_signs",
        sa.Column(
            "status",
            record_status,
            server_default="active",
            nullable=False,
        ),
    )
    op.alter_column("vital_signs", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("vital_signs", "status")
