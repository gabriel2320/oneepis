"""add auth security tables

Revision ID: 202606200016
Revises: 202606200015
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200016"
down_revision = "202606200015"
branch_labels = None
depends_on = None


auth_security_event_action = postgresql.ENUM(
    "login_succeeded",
    "login_failed",
    "login_blocked",
    "password_recovery_requested",
    "unlock_requested",
    "password_recovery_confirmed",
    "unlock_confirmed",
    name="auth_security_event_action",
    create_type=False,
)

auth_recovery_purpose = postgresql.ENUM(
    "password_recovery",
    "unlock",
    name="auth_recovery_purpose",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    auth_security_event_action.create(bind, checkfirst=True)
    auth_recovery_purpose.create(bind, checkfirst=True)

    op.create_table(
        "auth_security_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("action", auth_security_event_action, nullable=False),
        sa.Column("identifier_hash", sa.String(length=128), nullable=False),
        sa.Column("actor_id", sa.String(length=120), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=320), nullable=True),
        sa.Column("reason", sa.String(length=160), nullable=False),
        sa.Column("correlation_id", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auth_security_events_identifier_hash"),
        "auth_security_events",
        ["identifier_hash"],
    )
    op.create_index(
        op.f("ix_auth_security_events_correlation_id"),
        "auth_security_events",
        ["correlation_id"],
    )
    op.create_index(
        op.f("ix_auth_security_events_created_at"),
        "auth_security_events",
        ["created_at"],
    )

    op.create_table(
        "auth_login_locks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("identifier_hash", sa.String(length=128), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("identifier_hash"),
    )
    op.create_index(
        op.f("ix_auth_login_locks_locked_until"),
        "auth_login_locks",
        ["locked_until"],
    )

    op.create_table(
        "auth_recovery_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("purpose", auth_recovery_purpose, nullable=False),
        sa.Column("identifier_hash", sa.String(length=128), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_auth_recovery_tokens_identifier_hash"),
        "auth_recovery_tokens",
        ["identifier_hash"],
    )
    op.create_index(
        op.f("ix_auth_recovery_tokens_expires_at"),
        "auth_recovery_tokens",
        ["expires_at"],
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.String(length=120), nullable=False),
        sa.Column("identifier_hash", sa.String(length=128), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index(op.f("ix_auth_sessions_actor_id"), "auth_sessions", ["actor_id"])
    op.create_index(
        op.f("ix_auth_sessions_identifier_hash"),
        "auth_sessions",
        ["identifier_hash"],
    )
    op.create_index(op.f("ix_auth_sessions_expires_at"), "auth_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_sessions_expires_at"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_identifier_hash"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_actor_id"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index(
        op.f("ix_auth_recovery_tokens_expires_at"),
        table_name="auth_recovery_tokens",
    )
    op.drop_index(
        op.f("ix_auth_recovery_tokens_identifier_hash"),
        table_name="auth_recovery_tokens",
    )
    op.drop_table("auth_recovery_tokens")
    op.drop_index(op.f("ix_auth_login_locks_locked_until"), table_name="auth_login_locks")
    op.drop_table("auth_login_locks")
    op.drop_index(op.f("ix_auth_security_events_created_at"), table_name="auth_security_events")
    op.drop_index(op.f("ix_auth_security_events_correlation_id"), table_name="auth_security_events")
    op.drop_index(
        op.f("ix_auth_security_events_identifier_hash"),
        table_name="auth_security_events",
    )
    op.drop_table("auth_security_events")

    bind = op.get_bind()
    auth_recovery_purpose.drop(bind, checkfirst=True)
    auth_security_event_action.drop(bind, checkfirst=True)
