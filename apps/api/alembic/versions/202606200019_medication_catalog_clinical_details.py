"""medication catalog clinical details

Revision ID: 202606200019
Revises: 202606200018
Create Date: 2026-06-29
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200019"
down_revision = "202606200018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    empty_list = sa.text("'[]'::jsonb")
    op.add_column(
        "medication_catalog_items",
        sa.Column(
            "clinical_uses",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=empty_list,
            nullable=False,
        ),
    )
    op.add_column(
        "medication_catalog_items",
        sa.Column(
            "administration_routes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=empty_list,
            nullable=False,
        ),
    )
    op.add_column(
        "medication_catalog_items",
        sa.Column(
            "interaction_alerts",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=empty_list,
            nullable=False,
        ),
    )
    op.add_column(
        "medication_catalog_items",
        sa.Column(
            "safety_alerts",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=empty_list,
            nullable=False,
        ),
    )
    op.add_column(
        "medication_catalog_items",
        sa.Column(
            "monitoring_notes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=empty_list,
            nullable=False,
        ),
    )
    for column_name in (
        "clinical_uses",
        "administration_routes",
        "interaction_alerts",
        "safety_alerts",
        "monitoring_notes",
    ):
        op.alter_column("medication_catalog_items", column_name, server_default=None)


def downgrade() -> None:
    op.drop_column("medication_catalog_items", "monitoring_notes")
    op.drop_column("medication_catalog_items", "safety_alerts")
    op.drop_column("medication_catalog_items", "interaction_alerts")
    op.drop_column("medication_catalog_items", "administration_routes")
    op.drop_column("medication_catalog_items", "clinical_uses")
