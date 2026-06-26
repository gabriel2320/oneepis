"""add encounter workflow kind

Revision ID: 202606200017
Revises: 202606200016
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200017"
down_revision = "202606200016"
branch_labels = None
depends_on = None


encounter_workflow_kind = postgresql.ENUM(
    "general",
    "ambulatory_preconsult",
    "ambulatory_visit",
    "hospitalization_admission",
    "hospitalization_daily",
    "hospitalization_discharge",
    name="encounter_workflow_kind",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    encounter_workflow_kind.create(bind, checkfirst=True)
    op.add_column(
        "clinical_encounters",
        sa.Column(
            "workflow_kind",
            encounter_workflow_kind,
            server_default="general",
            nullable=False,
        ),
    )
    op.alter_column("clinical_encounters", "workflow_kind", server_default=None)


def downgrade() -> None:
    op.drop_column("clinical_encounters", "workflow_kind")
    bind = op.get_bind()
    encounter_workflow_kind.drop(bind, checkfirst=True)
