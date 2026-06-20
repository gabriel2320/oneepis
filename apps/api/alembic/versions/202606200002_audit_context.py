"""audit request context

Revision ID: 202606200002
Revises: 202606200001
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "202606200002"
down_revision = "202606200001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_events", sa.Column("correlation_id", sa.String(length=80), nullable=True))
    op.add_column("audit_events", sa.Column("request_method", sa.String(length=12), nullable=True))
    op.add_column("audit_events", sa.Column("request_path", sa.String(length=240), nullable=True))
    op.create_index("ix_audit_events_correlation_id", "audit_events", ["correlation_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_correlation_id", table_name="audit_events")
    op.drop_column("audit_events", "request_path")
    op.drop_column("audit_events", "request_method")
    op.drop_column("audit_events", "correlation_id")
