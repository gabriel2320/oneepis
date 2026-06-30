"""care team service boundaries

Revision ID: 202606200023
Revises: 202606200022
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200023"
down_revision = "202606200022"
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
    op.create_table(
        "clinical_services",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["clinical_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_clinical_services_tenant_key"),
    )
    op.create_index(
        op.f("ix_clinical_services_tenant_id"),
        "clinical_services",
        ["tenant_id"],
        unique=False,
    )
    op.create_table(
        "care_teams",
        sa.Column("service_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["service_id"], ["clinical_services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_id", "key", name="uq_care_teams_service_key"),
    )
    op.create_index(
        op.f("ix_care_teams_service_id"),
        "care_teams",
        ["service_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_care_teams_service_id"), table_name="care_teams")
    op.drop_table("care_teams")
    op.drop_index(op.f("ix_clinical_services_tenant_id"), table_name="clinical_services")
    op.drop_table("clinical_services")
