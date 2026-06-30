"""actor care team memberships

Revision ID: 202606200025
Revises: 202606200024
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200025"
down_revision = "202606200024"
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
        "actor_care_team_memberships",
        sa.Column("actor_id", sa.String(length=120), nullable=False),
        sa.Column("care_team_id", sa.Uuid(), nullable=False),
        sa.Column("status", access_boundary_status, nullable=False),
        sa.Column("membership_reason", sa.String(length=240), nullable=True),
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
        sa.ForeignKeyConstraint(["care_team_id"], ["care_teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("actor_id", "care_team_id", name="uq_actor_care_team_membership"),
    )
    op.create_index(
        op.f("ix_actor_care_team_memberships_actor_id"),
        "actor_care_team_memberships",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_actor_care_team_memberships_care_team_id"),
        "actor_care_team_memberships",
        ["care_team_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_actor_care_team_memberships_care_team_id"),
        table_name="actor_care_team_memberships",
    )
    op.drop_index(
        op.f("ix_actor_care_team_memberships_actor_id"),
        table_name="actor_care_team_memberships",
    )
    op.drop_table("actor_care_team_memberships")
