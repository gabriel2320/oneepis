"""access boundaries

Revision ID: 202606200022
Revises: 202606200021
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200022"
down_revision = "202606200021"
branch_labels = None
depends_on = None

access_boundary_status = postgresql.ENUM(
    "draft",
    "active",
    "retired",
    name="access_boundary_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    access_boundary_status.create(bind, checkfirst=True)
    op.create_table(
        "clinical_institutions",
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("status", access_boundary_status, nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.UniqueConstraint("key", name="uq_clinical_institutions_key"),
    )
    op.create_table(
        "clinical_tenants",
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("status", access_boundary_status, nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
            ["institution_id"],
            ["clinical_institutions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "institution_id",
            "key",
            name="uq_clinical_tenants_institution_key",
        ),
    )
    op.create_index(
        op.f("ix_clinical_tenants_institution_id"),
        "clinical_tenants",
        ["institution_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_tenants_institution_id"), table_name="clinical_tenants")
    op.drop_table("clinical_tenants")
    op.drop_table("clinical_institutions")
    bind = op.get_bind()
    access_boundary_status.drop(bind, checkfirst=True)
