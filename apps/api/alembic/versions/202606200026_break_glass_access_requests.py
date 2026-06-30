"""add disabled break glass access request store

Revision ID: 202606200026
Revises: 202606200025
Create Date: 2026-06-20 00:26:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200026"
down_revision = "202606200025"
branch_labels = None
depends_on = None

access_boundary_status = postgresql.ENUM(
    "draft",
    "active",
    "retired",
    name="access_boundary_status",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "break_glass_access_requests",
        sa.Column("actor_id", sa.String(length=120), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("correlation_id", sa.String(length=80), nullable=True),
        sa.Column("reason_code", sa.String(length=80), nullable=False),
        sa.Column("status", access_boundary_status, nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_break_glass_access_requests_actor_id"),
        "break_glass_access_requests",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_break_glass_access_requests_correlation_id"),
        "break_glass_access_requests",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_break_glass_access_requests_patient_id"),
        "break_glass_access_requests",
        ["patient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_break_glass_access_requests_patient_id"),
        table_name="break_glass_access_requests",
    )
    op.drop_index(
        op.f("ix_break_glass_access_requests_correlation_id"),
        table_name="break_glass_access_requests",
    )
    op.drop_index(
        op.f("ix_break_glass_access_requests_actor_id"),
        table_name="break_glass_access_requests",
    )
    op.drop_table("break_glass_access_requests")
