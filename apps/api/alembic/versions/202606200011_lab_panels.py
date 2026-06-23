"""structured lab panels

Revision ID: 202606200011
Revises: 202606200010
Create Date: 2026-06-23
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200011"
down_revision = "202606200010"
branch_labels = None
depends_on = None


clinical_event_source_type = postgresql.ENUM(
    "manual",
    "clinical_entry",
    "vital_sign",
    "imported_document",
    "ai_draft",
    name="clinical_event_source_type",
    create_type=False,
)

record_status = postgresql.ENUM(
    "active",
    "inactive",
    "resolved",
    "entered_in_error",
    name="record_status",
    create_type=False,
)

lab_result_flag = postgresql.ENUM(
    "low",
    "normal",
    "high",
    "critical",
    "abnormal",
    "unknown",
    name="lab_result_flag",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    lab_result_flag.create(bind, checkfirst=True)

    op.create_table(
        "lab_panels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("panel_name", sa.String(length=160), nullable=False),
        sa.Column("source_type", clinical_event_source_type, nullable=False),
        sa.Column("source_ref", sa.String(length=160), nullable=True),
        sa.Column("status", record_status, nullable=False),
        sa.Column("summary", sa.String(length=280), nullable=True),
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
        sa.ForeignKeyConstraint(["encounter_id"], ["clinical_encounters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lab_panels_encounter_id"), "lab_panels", ["encounter_id"])
    op.create_index(op.f("ix_lab_panels_occurred_at"), "lab_panels", ["occurred_at"])
    op.create_index(op.f("ix_lab_panels_patient_id"), "lab_panels", ["patient_id"])

    op.create_table(
        "lab_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("panel_id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("value", sa.String(length=80), nullable=True),
        sa.Column("numeric_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("reference_range", sa.String(length=120), nullable=True),
        sa.Column("flag", lab_result_flag, nullable=False),
        sa.Column("status", record_status, nullable=False),
        sa.Column("notes", sa.String(length=240), nullable=True),
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
        sa.ForeignKeyConstraint(["panel_id"], ["lab_panels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lab_results_code"), "lab_results", ["code"])
    op.create_index(op.f("ix_lab_results_panel_id"), "lab_results", ["panel_id"])
    op.create_index(op.f("ix_lab_results_patient_id"), "lab_results", ["patient_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_lab_results_patient_id"), table_name="lab_results")
    op.drop_index(op.f("ix_lab_results_panel_id"), table_name="lab_results")
    op.drop_index(op.f("ix_lab_results_code"), table_name="lab_results")
    op.drop_table("lab_results")

    op.drop_index(op.f("ix_lab_panels_patient_id"), table_name="lab_panels")
    op.drop_index(op.f("ix_lab_panels_occurred_at"), table_name="lab_panels")
    op.drop_index(op.f("ix_lab_panels_encounter_id"), table_name="lab_panels")
    op.drop_table("lab_panels")

    bind = op.get_bind()
    lab_result_flag.drop(bind, checkfirst=True)
