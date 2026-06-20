"""hospital beds

Revision ID: 202606200006
Revises: 202606200005
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200006"
down_revision = "202606200005"
branch_labels = None
depends_on = None


hospital_bed_status = postgresql.ENUM(
    "available",
    "occupied",
    "cleaning",
    "blocked",
    name="hospital_bed_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    hospital_bed_status.create(bind, checkfirst=True)

    op.create_table(
        "hospital_beds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ward", sa.String(length=80), nullable=False),
        sa.Column("room", sa.String(length=80), nullable=False),
        sa.Column("bed_label", sa.String(length=80), nullable=False),
        sa.Column("status", hospital_bed_status, nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["clinical_encounters.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("encounter_id"),
        sa.UniqueConstraint("ward", "room", "bed_label", name="uq_hospital_beds_location"),
    )


def downgrade() -> None:
    op.drop_table("hospital_beds")

    bind = op.get_bind()
    hospital_bed_status.drop(bind, checkfirst=True)
