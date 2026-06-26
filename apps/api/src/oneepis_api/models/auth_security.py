from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.patient import enum_values


class AuthSecurityEventAction(enum.StrEnum):
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_FAILED = "login_failed"
    LOGIN_BLOCKED = "login_blocked"
    PASSWORD_RECOVERY_REQUESTED = "password_recovery_requested"
    UNLOCK_REQUESTED = "unlock_requested"
    PASSWORD_RECOVERY_CONFIRMED = "password_recovery_confirmed"
    UNLOCK_CONFIRMED = "unlock_confirmed"


class AuthRecoveryPurpose(enum.StrEnum):
    PASSWORD_RECOVERY = "password_recovery"
    UNLOCK = "unlock"


class AuthSecurityEvent(Base, IdMixin):
    __tablename__ = "auth_security_events"

    action: Mapped[AuthSecurityEventAction] = mapped_column(
        Enum(
            AuthSecurityEventAction,
            values_callable=enum_values,
            name="auth_security_event_action",
        ),
        nullable=False,
    )
    identifier_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(320), nullable=True)
    reason: Mapped[str] = mapped_column(String(160), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )


class AuthLoginLock(Base, IdMixin, TimestampMixin):
    __tablename__ = "auth_login_locks"

    identifier_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )


class AuthRecoveryToken(Base, IdMixin, TimestampMixin):
    __tablename__ = "auth_recovery_tokens"

    purpose: Mapped[AuthRecoveryPurpose] = mapped_column(
        Enum(
            AuthRecoveryPurpose,
            values_callable=enum_values,
            name="auth_recovery_purpose",
        ),
        nullable=False,
    )
    identifier_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuthSession(Base, IdMixin, TimestampMixin):
    __tablename__ = "auth_sessions"

    actor_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    identifier_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
