"""clinical entry entered in error status

Revision ID: 202606200020
Revises: 202606200019
Create Date: 2026-06-29
"""

from __future__ import annotations

from alembic import op

revision = "202606200020"
down_revision = "202606200019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE clinical_entry_status ADD VALUE IF NOT EXISTS 'entered_in_error'")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("UPDATE clinical_entries SET status = 'draft' WHERE status = 'entered_in_error'")
    op.execute("ALTER TABLE clinical_entries ALTER COLUMN status TYPE text USING status::text")
    op.execute("DROP TYPE clinical_entry_status")
    op.execute("CREATE TYPE clinical_entry_status AS ENUM ('draft', 'signed', 'amended')")
    op.execute(
        "ALTER TABLE clinical_entries "
        "ALTER COLUMN status TYPE clinical_entry_status "
        "USING status::clinical_entry_status"
    )
