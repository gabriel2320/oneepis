"""clinical events

Revision ID: 202606200010
Revises: 202606200009
Create Date: 2026-06-22
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200010"
down_revision = "202606200009"
branch_labels = None
depends_on = None


clinical_event_type = postgresql.ENUM(
    "symptom",
    "vital_sign",
    "exam_result",
    "diagnosis",
    "medication",
    "procedure",
    "clinical_note",
    "care_plan",
    "administrative",
    name="clinical_event_type",
    create_type=False,
)

clinical_event_source_type = postgresql.ENUM(
    "manual",
    "clinical_entry",
    "vital_sign",
    "imported_document",
    "ai_draft",
    name="clinical_event_source_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    clinical_event_type.create(bind, checkfirst=True)
    clinical_event_source_type.create(bind, checkfirst=True)

    op.create_table(
        "clinical_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", clinical_event_type, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.String(length=280), nullable=False),
        sa.Column("source_type", clinical_event_source_type, nullable=False),
        sa.Column("source_ref", sa.String(length=160), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
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
    op.create_index(op.f("ix_clinical_events_encounter_id"), "clinical_events", ["encounter_id"])
    op.create_index(op.f("ix_clinical_events_occurred_at"), "clinical_events", ["occurred_at"])
    op.create_index(op.f("ix_clinical_events_patient_id"), "clinical_events", ["patient_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_events_patient_id"), table_name="clinical_events")
    op.drop_index(op.f("ix_clinical_events_occurred_at"), table_name="clinical_events")
    op.drop_index(op.f("ix_clinical_events_encounter_id"), table_name="clinical_events")
    op.drop_table("clinical_events")

    bind = op.get_bind()
    clinical_event_source_type.drop(bind, checkfirst=True)
    clinical_event_type.drop(bind, checkfirst=True)
