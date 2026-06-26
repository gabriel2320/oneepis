from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings
from oneepis_api.models.auth_security import (
    AuthLoginLock,
    AuthSecurityEvent,
    AuthSecurityEventAction,
)
from oneepis_api.services.audit import get_audit_request_context


@dataclass(frozen=True)
class AuthRequestMetadata:
    ip_address: str | None = None
    user_agent: str | None = None


def identifier_hash(settings: Settings, identifier: str) -> str:
    normalized = identifier.strip().lower()
    digest = hmac.new(
        settings.auth_secret.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def is_login_locked(
    session: Session,
    settings: Settings,
    identifier: str,
    now: datetime | None = None,
) -> bool:
    current_time = now or datetime.now(UTC)
    lock = _get_lock(session, settings, identifier)
    locked_until = as_aware_datetime(lock.locked_until) if lock and lock.locked_until else None
    return bool(locked_until and locked_until > current_time)


def record_login_success(
    session: Session,
    settings: Settings,
    *,
    identifier: str,
    actor_id: str,
    metadata: AuthRequestMetadata,
    now: datetime | None = None,
) -> None:
    identifier_digest = identifier_hash(settings, identifier)
    lock = _get_lock_by_hash(session, identifier_digest)
    if lock:
        lock.failed_attempts = 0
        lock.first_failed_at = None
        lock.locked_until = None
    record_auth_security_event(
        session,
        settings,
        action=AuthSecurityEventAction.LOGIN_SUCCEEDED,
        identifier=identifier,
        actor_id=actor_id,
        reason="valid_credentials",
        metadata=metadata,
        now=now,
    )


def record_login_failure(
    session: Session,
    settings: Settings,
    *,
    identifier: str,
    metadata: AuthRequestMetadata,
    now: datetime | None = None,
) -> bool:
    current_time = now or datetime.now(UTC)
    identifier_digest = identifier_hash(settings, identifier)
    lock = _get_lock_by_hash(session, identifier_digest)
    if lock is None:
        lock = AuthLoginLock(identifier_hash=identifier_digest, failed_attempts=0)
        session.add(lock)

    window_started_at = current_time - timedelta(seconds=settings.auth_login_window_seconds)
    first_failed_at = as_aware_datetime(lock.first_failed_at) if lock.first_failed_at else None
    if first_failed_at is None or first_failed_at < window_started_at:
        lock.failed_attempts = 0
        lock.first_failed_at = current_time

    lock.failed_attempts += 1
    locked = lock.failed_attempts >= settings.auth_login_max_failed_attempts
    if locked:
        lock.locked_until = current_time + timedelta(seconds=settings.auth_login_lock_seconds)

    event_action = (
        AuthSecurityEventAction.LOGIN_BLOCKED if locked else AuthSecurityEventAction.LOGIN_FAILED
    )
    record_auth_security_event(
        session,
        settings,
        action=event_action,
        identifier=identifier,
        actor_id=None,
        reason="too_many_failed_attempts" if locked else "invalid_credentials",
        metadata=metadata,
        now=current_time,
    )
    return locked


def record_blocked_login_attempt(
    session: Session,
    settings: Settings,
    *,
    identifier: str,
    metadata: AuthRequestMetadata,
    now: datetime | None = None,
) -> None:
    record_auth_security_event(
        session,
        settings,
        action=AuthSecurityEventAction.LOGIN_BLOCKED,
        identifier=identifier,
        actor_id=None,
        reason="temporary_lock_active",
        metadata=metadata,
        now=now,
    )


def record_auth_security_event(
    session: Session,
    settings: Settings,
    *,
    action: AuthSecurityEventAction,
    identifier: str,
    actor_id: str | None,
    reason: str,
    metadata: AuthRequestMetadata,
    now: datetime | None = None,
) -> None:
    context = get_audit_request_context()
    session.add(
        AuthSecurityEvent(
            action=action,
            identifier_hash=identifier_hash(settings, identifier),
            actor_id=actor_id,
            ip_address=_truncate(metadata.ip_address, 80),
            user_agent=_truncate(metadata.user_agent, 320),
            reason=reason,
            correlation_id=context.correlation_id if context else None,
            created_at=now or datetime.now(UTC),
        )
    )


def record_auth_security_event_by_hash(
    session: Session,
    *,
    action: AuthSecurityEventAction,
    identifier_digest: str,
    actor_id: str | None,
    reason: str,
    metadata: AuthRequestMetadata,
    now: datetime,
) -> None:
    context = get_audit_request_context()
    session.add(
        AuthSecurityEvent(
            action=action,
            identifier_hash=identifier_digest,
            actor_id=actor_id,
            ip_address=_truncate(metadata.ip_address, 80),
            user_agent=_truncate(metadata.user_agent, 320),
            reason=reason,
            correlation_id=context.correlation_id if context else None,
            created_at=now,
        )
    )


def clear_login_lock_by_hash(session: Session, identifier_digest: str) -> None:
    lock = _get_lock_by_hash(session, identifier_digest)
    if not lock:
        return
    lock.failed_attempts = 0
    lock.first_failed_at = None
    lock.locked_until = None


def as_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _get_lock(session: Session, settings: Settings, identifier: str) -> AuthLoginLock | None:
    return _get_lock_by_hash(session, identifier_hash(settings, identifier))


def _get_lock_by_hash(session: Session, digest: str) -> AuthLoginLock | None:
    return session.scalar(select(AuthLoginLock).where(AuthLoginLock.identifier_hash == digest))


def _truncate(value: str | None, length: int) -> str | None:
    if not value:
        return None
    return value[:length]

