"""add discharge summary clinical entry kind

Revision ID: 202606200013
Revises: 202606200012
Create Date: 2026-06-20
"""

from __future__ import annotations

from alembic import op

revision = "202606200013"
down_revision = "202606200012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE clinical_entry_kind ADD VALUE IF NOT EXISTS 'discharge_summary'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding the type.
    pass
