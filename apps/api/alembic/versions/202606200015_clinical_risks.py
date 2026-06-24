"""add clinical risks

Revision ID: 202606200015
Revises: 202606200014
Create Date: 2026-06-23
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200015"
down_revision = "202606200014"
branch_labels = None
depends_on = None


clinical_risk_type = postgresql.ENUM(
    "fall",
    "pressure_injury",
    "vte",
    "isolation",
    "adverse_event",
    "other",
    name="clinical_risk_type",
    create_type=False,
)

clinical_risk_severity = postgresql.ENUM(
    "low",
    "moderate",
    "high",
    "critical",
    "unknown",
    name="clinical_risk_severity",
    create_type=False,
)

clinical_risk_source_kind = postgresql.ENUM(
    "manual",
    "vital_sign",
    "clinical_event",
    "clinical_entry",
    "lab_result",
    name="clinical_risk_source_kind",
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


def upgrade() -> None:
    bind = op.get_bind()
    clinical_risk_type.create(bind, checkfirst=True)
    clinical_risk_severity.create(bind, checkfirst=True)
    clinical_risk_source_kind.create(bind, checkfirst=True)

    op.create_table(
        "clinical_risks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=True),
        sa.Column("risk_type", clinical_risk_type, nullable=False),
        sa.Column("severity", clinical_risk_severity, nullable=False),
        sa.Column("status", record_status, nullable=False),
        sa.Column("source_kind", clinical_risk_source_kind, nullable=False),
        sa.Column("source_ref", sa.String(length=160), nullable=True),
        sa.Column("reason", sa.String(length=320), nullable=False),
        sa.Column("human_action", sa.String(length=320), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(op.f("ix_clinical_risks_encounter_id"), "clinical_risks", ["encounter_id"])
    op.create_index(op.f("ix_clinical_risks_patient_id"), "clinical_risks", ["patient_id"])
    op.create_index(op.f("ix_clinical_risks_risk_type"), "clinical_risks", ["risk_type"])


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_risks_risk_type"), table_name="clinical_risks")
    op.drop_index(op.f("ix_clinical_risks_patient_id"), table_name="clinical_risks")
    op.drop_index(op.f("ix_clinical_risks_encounter_id"), table_name="clinical_risks")
    op.drop_table("clinical_risks")

    bind = op.get_bind()
    clinical_risk_source_kind.drop(bind, checkfirst=True)
    clinical_risk_severity.drop(bind, checkfirst=True)
    clinical_risk_type.drop(bind, checkfirst=True)
