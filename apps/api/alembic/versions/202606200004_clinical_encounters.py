"""clinical encounters

Revision ID: 202606200004
Revises: 202606200003
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200004"
down_revision = "202606200003"
branch_labels = None
depends_on = None


encounter_type = postgresql.ENUM(
    "ambulatory",
    "hospitalization",
    "emergency",
    "unknown",
    name="encounter_type",
    create_type=False,
)
encounter_status = postgresql.ENUM(
    "scheduled",
    "in_progress",
    "completed",
    "cancelled",
    name="encounter_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    encounter_type.create(bind, checkfirst=True)
    encounter_status.create(bind, checkfirst=True)

    op.create_table(
        "clinical_encounters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("type", encounter_type, nullable=False),
        sa.Column("status", encounter_status, nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location_label", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.String(length=320), nullable=True),
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
    op.create_index("ix_clinical_encounters_patient_id", "clinical_encounters", ["patient_id"])
    op.create_index("ix_clinical_encounters_started_at", "clinical_encounters", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_clinical_encounters_started_at", table_name="clinical_encounters")
    op.drop_index("ix_clinical_encounters_patient_id", table_name="clinical_encounters")
    op.drop_table("clinical_encounters")

    bind = op.get_bind()
    encounter_status.drop(bind, checkfirst=True)
    encounter_type.drop(bind, checkfirst=True)
