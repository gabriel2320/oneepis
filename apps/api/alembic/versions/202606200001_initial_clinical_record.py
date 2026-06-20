"""initial clinical record

Revision ID: 202606200001
Revises:
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200001"
down_revision = None
branch_labels = None
depends_on = None


sex_at_birth = sa.Enum("female", "male", "intersex", "unknown", name="sex_at_birth")
entry_kind = sa.Enum(
    "intake",
    "progress",
    "lab_result",
    "prescription",
    "procedure",
    "note",
    name="clinical_entry_kind",
)
entry_status = sa.Enum("draft", "signed", "amended", name="clinical_entry_status")
allergy_severity = sa.Enum("mild", "moderate", "severe", "unknown", name="allergy_severity")
record_status = sa.Enum("active", "inactive", "resolved", "entered_in_error", name="record_status")


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("preferred_name", sa.String(length=80), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("sex_at_birth", sex_at_birth, nullable=False),
        sa.Column("document_id_hash", sa.String(length=128), nullable=True),
        sa.Column("clinical_identifier", sa.String(length=64), nullable=True),
        sa.Column("contact_phone", sa.String(length=40), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("emergency_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patients_clinical_identifier", "patients", ["clinical_identifier"], unique=True
    )
    op.create_index("ix_patients_document_id_hash", "patients", ["document_id_hash"], unique=True)
    op.create_index("ix_patients_last_name", "patients", ["last_name"], unique=False)

    op.create_table(
        "clinical_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("kind", entry_kind, nullable=False),
        sa.Column("status", entry_status, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("subjective", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("assessment", sa.Text(), nullable=True),
        sa.Column("plan", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        "ix_clinical_entries_patient_id", "clinical_entries", ["patient_id"], unique=False
    )
    op.create_index(
        "ix_clinical_entries_occurred_at", "clinical_entries", ["occurred_at"], unique=False
    )

    op.create_table(
        "allergies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("substance", sa.String(length=160), nullable=False),
        sa.Column("reaction", sa.String(length=240), nullable=True),
        sa.Column("severity", allergy_severity, nullable=False),
        sa.Column("status", record_status, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
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
    op.create_index("ix_allergies_patient_id", "allergies", ["patient_id"], unique=False)

    op.create_table(
        "medications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("dose", sa.String(length=120), nullable=True),
        sa.Column("route", sa.String(length=80), nullable=True),
        sa.Column("frequency", sa.String(length=120), nullable=True),
        sa.Column("status", record_status, nullable=False),
        sa.Column("started_on", sa.Date(), nullable=True),
        sa.Column("ended_on", sa.Date(), nullable=True),
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
    op.create_index("ix_medications_patient_id", "medications", ["patient_id"], unique=False)

    op.create_table(
        "vital_signs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("systolic_bp", sa.Integer(), nullable=True),
        sa.Column("diastolic_bp", sa.Integer(), nullable=True),
        sa.Column("heart_rate_bpm", sa.Integer(), nullable=True),
        sa.Column("respiratory_rate_bpm", sa.Integer(), nullable=True),
        sa.Column("oxygen_saturation_pct", sa.Numeric(precision=5, scale=2), nullable=True),
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
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vital_signs_patient_id", "vital_signs", ["patient_id"], unique=False)
    op.create_index("ix_vital_signs_measured_at", "vital_signs", ["measured_at"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("actor_id", sa.String(length=120), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_entity", "audit_events", ["entity_type", "entity_id"], unique=False
    )
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_entity", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_vital_signs_measured_at", table_name="vital_signs")
    op.drop_index("ix_vital_signs_patient_id", table_name="vital_signs")
    op.drop_table("vital_signs")

    op.drop_index("ix_medications_patient_id", table_name="medications")
    op.drop_table("medications")

    op.drop_index("ix_allergies_patient_id", table_name="allergies")
    op.drop_table("allergies")

    op.drop_index("ix_clinical_entries_occurred_at", table_name="clinical_entries")
    op.drop_index("ix_clinical_entries_patient_id", table_name="clinical_entries")
    op.drop_table("clinical_entries")

    op.drop_index("ix_patients_last_name", table_name="patients")
    op.drop_index("ix_patients_document_id_hash", table_name="patients")
    op.drop_index("ix_patients_clinical_identifier", table_name="patients")
    op.drop_table("patients")

    bind = op.get_bind()
    record_status.drop(bind, checkfirst=True)
    allergy_severity.drop(bind, checkfirst=True)
    entry_status.drop(bind, checkfirst=True)
    entry_kind.drop(bind, checkfirst=True)
    sex_at_birth.drop(bind, checkfirst=True)
