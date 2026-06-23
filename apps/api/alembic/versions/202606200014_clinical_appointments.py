"""add clinical appointments

Revision ID: 202606200014
Revises: 202606200013
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "202606200014"
down_revision = "202606200013"
branch_labels = None
depends_on = None


appointment_status = sa.Enum(
    "scheduled",
    "check_in",
    "in_progress",
    "completed",
    "cancelled",
    "no_show",
    name="appointment_status",
)


def upgrade() -> None:
    op.create_table(
        "clinical_appointments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("status", appointment_status, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("location_label", sa.String(length=120), nullable=True),
        sa.Column("clinician_label", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.String(length=320), nullable=True),
        sa.Column("created_by", sa.String(length=120), nullable=False),
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
        "ix_clinical_appointments_patient_id",
        "clinical_appointments",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_clinical_appointments_starts_at",
        "clinical_appointments",
        ["starts_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_appointments_starts_at", table_name="clinical_appointments")
    op.drop_index("ix_clinical_appointments_patient_id", table_name="clinical_appointments")
    op.drop_table("clinical_appointments")
    appointment_status.drop(op.get_bind(), checkfirst=True)
