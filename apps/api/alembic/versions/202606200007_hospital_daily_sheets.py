"""hospital daily sheets

Revision ID: 202606200007
Revises: 202606200006
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "202606200007"
down_revision = "202606200006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hospital_daily_sheets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=False),
        sa.Column("sheet_date", sa.Date(), nullable=False),
        sa.Column("clinical_summary", sa.Text(), nullable=False),
        sa.Column("overnight_events", sa.Text(), nullable=True),
        sa.Column("active_plan", sa.Text(), nullable=True),
        sa.Column("pending_tasks", sa.Text(), nullable=True),
        sa.Column("safety_notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["encounter_id"], ["clinical_encounters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "encounter_id",
            "sheet_date",
            name="uq_hospital_daily_sheets_encounter_date",
        ),
    )
    op.create_index(
        op.f("ix_hospital_daily_sheets_encounter_id"),
        "hospital_daily_sheets",
        ["encounter_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hospital_daily_sheets_patient_id"),
        "hospital_daily_sheets",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hospital_daily_sheets_sheet_date"),
        "hospital_daily_sheets",
        ["sheet_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hospital_daily_sheets_sheet_date"), table_name="hospital_daily_sheets")
    op.drop_index(op.f("ix_hospital_daily_sheets_patient_id"), table_name="hospital_daily_sheets")
    op.drop_index(
        op.f("ix_hospital_daily_sheets_encounter_id"),
        table_name="hospital_daily_sheets",
    )
    op.drop_table("hospital_daily_sheets")
