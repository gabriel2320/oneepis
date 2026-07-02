"""add vital sign patient measured_at index

Revision ID: 202606200027
Revises: 202606200026
Create Date: 2026-07-02
"""

from __future__ import annotations

from alembic import op

revision = "202606200027"
down_revision = "202606200026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_vital_signs_patient_id_measured_at",
        "vital_signs",
        ["patient_id", "measured_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vital_signs_patient_id_measured_at",
        table_name="vital_signs",
    )
