"""link clinical entries to encounters

Revision ID: 202606200005
Revises: 202606200004
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "202606200005"
down_revision = "202606200004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clinical_entries", sa.Column("encounter_id", sa.Uuid(), nullable=True))
    op.create_index("ix_clinical_entries_encounter_id", "clinical_entries", ["encounter_id"])
    op.create_foreign_key(
        "fk_clinical_entries_encounter_id",
        "clinical_entries",
        "clinical_encounters",
        ["encounter_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_clinical_entries_encounter_id", "clinical_entries", type_="foreignkey")
    op.drop_index("ix_clinical_entries_encounter_id", table_name="clinical_entries")
    op.drop_column("clinical_entries", "encounter_id")
