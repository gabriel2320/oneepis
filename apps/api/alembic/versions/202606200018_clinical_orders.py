"""clinical orders draft

Revision ID: 202606200018
Revises: 202606200017
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200018"
down_revision = "202606200017"
branch_labels = None
depends_on = None

clinical_order_status = postgresql.ENUM(
    "draft",
    "cancelled",
    "entered_in_error",
    name="clinical_order_status",
    create_type=False,
)
clinical_order_kind = postgresql.ENUM(
    "lab",
    "imaging",
    "nursing",
    "other",
    name="clinical_order_kind",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    clinical_order_status.create(bind, checkfirst=True)
    clinical_order_kind.create(bind, checkfirst=True)

    op.create_table(
        "clinical_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=False),
        sa.Column("status", clinical_order_status, nullable=False),
        sa.Column("kind", clinical_order_kind, nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("order_text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
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
        op.f("ix_clinical_orders_encounter_id"),
        "clinical_orders",
        ["encounter_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_orders_ordered_at"),
        "clinical_orders",
        ["ordered_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_orders_patient_id"),
        "clinical_orders",
        ["patient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_orders_patient_id"), table_name="clinical_orders")
    op.drop_index(op.f("ix_clinical_orders_ordered_at"), table_name="clinical_orders")
    op.drop_index(op.f("ix_clinical_orders_encounter_id"), table_name="clinical_orders")
    op.drop_table("clinical_orders")

    bind = op.get_bind()
    clinical_order_kind.drop(bind, checkfirst=True)
    clinical_order_status.drop(bind, checkfirst=True)
