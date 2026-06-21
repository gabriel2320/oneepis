"""hospital daily sheet status

Revision ID: 202606200008
Revises: 202606200007
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200008"
down_revision = "202606200007"
branch_labels = None
depends_on = None


hospital_daily_sheet_status = postgresql.ENUM(
    "draft",
    "closed",
    name="hospital_daily_sheet_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    hospital_daily_sheet_status.create(bind, checkfirst=True)

    op.add_column(
        "hospital_daily_sheets",
        sa.Column(
            "status",
            hospital_daily_sheet_status,
            server_default="draft",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("hospital_daily_sheets", "status")

    bind = op.get_bind()
    hospital_daily_sheet_status.drop(bind, checkfirst=True)
