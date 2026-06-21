"""hospital indications

Revision ID: 202606200009
Revises: 202606200008
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200009"
down_revision = "202606200008"
branch_labels = None
depends_on = None


hospital_indication_status = postgresql.ENUM(
    "draft",
    "closed",
    name="hospital_indication_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    hospital_indication_status.create(bind, checkfirst=True)

    op.create_table(
        "hospital_indications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=False),
        sa.Column("status", hospital_indication_status, nullable=False),
        sa.Column("indicated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("indication_text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
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
    )
    op.create_index(
        op.f("ix_hospital_indications_encounter_id"),
        "hospital_indications",
        ["encounter_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hospital_indications_indicated_at"),
        "hospital_indications",
        ["indicated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hospital_indications_patient_id"),
        "hospital_indications",
        ["patient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hospital_indications_patient_id"), table_name="hospital_indications")
    op.drop_index(op.f("ix_hospital_indications_indicated_at"), table_name="hospital_indications")
    op.drop_index(
        op.f("ix_hospital_indications_encounter_id"),
        table_name="hospital_indications",
    )
    op.drop_table("hospital_indications")

    bind = op.get_bind()
    hospital_indication_status.drop(bind, checkfirst=True)
