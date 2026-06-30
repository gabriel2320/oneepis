"""patient care team relationships

Revision ID: 202606200024
Revises: 202606200023
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200024"
down_revision = "202606200023"
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
        "patient_care_team_relationships",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("care_team_id", sa.Uuid(), nullable=False),
        sa.Column("status", access_boundary_status, nullable=False),
        sa.Column("relationship_reason", sa.String(length=240), nullable=True),
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
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "patient_id",
            "care_team_id",
            name="uq_patient_care_team_relationship",
        ),
    )
    op.create_index(
        op.f("ix_patient_care_team_relationships_care_team_id"),
        "patient_care_team_relationships",
        ["care_team_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_patient_care_team_relationships_patient_id"),
        "patient_care_team_relationships",
        ["patient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_patient_care_team_relationships_patient_id"),
        table_name="patient_care_team_relationships",
    )
    op.drop_index(
        op.f("ix_patient_care_team_relationships_care_team_id"),
        table_name="patient_care_team_relationships",
    )
    op.drop_table("patient_care_team_relationships")
