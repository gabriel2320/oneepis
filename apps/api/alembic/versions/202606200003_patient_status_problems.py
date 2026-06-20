"""patient status and active problems

Revision ID: 202606200003
Revises: 202606200002
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200003"
down_revision = "202606200002"
branch_labels = None
depends_on = None


patient_clinical_status = postgresql.ENUM(
    "draft",
    "active",
    "closed",
    "archived",
    name="patient_clinical_status",
)
care_context = postgresql.ENUM(
    "ambulatory",
    "hospitalized",
    "unknown",
    name="care_context",
)
record_status = postgresql.ENUM(
    "active",
    "inactive",
    "resolved",
    "entered_in_error",
    name="record_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    patient_clinical_status.create(bind, checkfirst=True)
    care_context.create(bind, checkfirst=True)

    op.add_column(
        "patients",
        sa.Column(
            "clinical_status",
            patient_clinical_status,
            server_default="active",
            nullable=False,
        ),
    )
    op.add_column(
        "patients",
        sa.Column(
            "current_care_context",
            care_context,
            server_default="unknown",
            nullable=False,
        ),
    )

    op.create_table(
        "active_problems",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("code_system", sa.String(length=80), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=True),
        sa.Column("status", record_status, nullable=False),
        sa.Column("onset_date", sa.Date(), nullable=True),
        sa.Column("resolved_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(length=280), nullable=True),
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
    op.create_index("ix_active_problems_patient_id", "active_problems", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_active_problems_patient_id", table_name="active_problems")
    op.drop_table("active_problems")
    op.drop_column("patients", "current_care_context")
    op.drop_column("patients", "clinical_status")

    bind = op.get_bind()
    care_context.drop(bind, checkfirst=True)
    patient_clinical_status.drop(bind, checkfirst=True)
