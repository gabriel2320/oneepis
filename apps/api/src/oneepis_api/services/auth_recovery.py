from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings
from oneepis_api.models.auth_security import (
    AuthRecoveryPurpose,
    AuthRecoveryToken,
    AuthSecurityEvent,
    AuthSecurityEventAction,
)
from oneepis_api.services.auth_security import (
    AuthRequestMetadata,
    as_aware_datetime,
    clear_login_lock_by_hash,
    identifier_hash,
    record_auth_security_event,
    record_auth_security_event_by_hash,
)


@dataclass(frozen=True)
class AuthRecoveryDispatch:
    token: str
    expires_at: datetime
    purpose: AuthRecoveryPurpose


def create_recovery_request(
    session: Session,
    settings: Settings,
    *,
    identifier: str,
    purpose: AuthRecoveryPurpose,
    metadata: AuthRequestMetadata,
    now: datetime | None = None,
) -> AuthRecoveryDispatch | None:
    current_time = now or datetime.now(UTC)
    event_action = _request_event_action(purpose)
    if _is_recovery_rate_limited(
        session,
        settings,
        identifier=identifier,
        action=event_action,
        now=current_time,
    ):
        record_auth_security_event(
            session,
            settings,
            action=event_action,
            identifier=identifier,
            actor_id=None,
            reason="rate_limited",
            metadata=metadata,
            now=current_time,
        )
        return None

    raw_token = secrets.token_urlsafe(32)
    expires_at = current_time + timedelta(minutes=settings.auth_recovery_token_ttl_minutes)
    session.add(
        AuthRecoveryToken(
            purpose=purpose,
            identifier_hash=identifier_hash(settings, identifier),
            token_hash=_token_hash(settings, raw_token),
            expires_at=expires_at,
        )
    )
    record_auth_security_event(
        session,
        settings,
        action=event_action,
        identifier=identifier,
        actor_id=None,
        reason="request_accepted",
        metadata=metadata,
        now=current_time,
    )
    return AuthRecoveryDispatch(token=raw_token, expires_at=expires_at, purpose=purpose)


def consume_recovery_token(
    session: Session,
    settings: Settings,
    *,
    token: str,
    purpose: AuthRecoveryPurpose,
    metadata: AuthRequestMetadata,
    now: datetime | None = None,
) -> bool:
    current_time = now or datetime.now(UTC)
    event_action = _confirmation_event_action(purpose)
    token_row = session.scalar(
        select(AuthRecoveryToken).where(
            AuthRecoveryToken.token_hash == _token_hash(settings, token),
            AuthRecoveryToken.purpose == purpose,
        )
    )
    if token_row is None:
        record_auth_security_event(
            session,
            settings,
            action=event_action,
            identifier="unknown-token",
            actor_id=None,
            reason="token_invalid",
            metadata=metadata,
            now=current_time,
        )
        return False

    expires_at = as_aware_datetime(token_row.expires_at)
    if token_row.used_at is not None or expires_at <= current_time:
        _record_token_event(
            session,
            token_row,
            event_action,
            "token_unavailable",
            metadata,
            current_time,
        )
        return False

    token_row.used_at = current_time
    if purpose == AuthRecoveryPurpose.UNLOCK:
        clear_login_lock_by_hash(session, token_row.identifier_hash)
    _record_token_event(session, token_row, event_action, "token_consumed", metadata, current_time)
    return True


def _request_event_action(purpose: AuthRecoveryPurpose) -> AuthSecurityEventAction:
    if purpose == AuthRecoveryPurpose.PASSWORD_RECOVERY:
        return AuthSecurityEventAction.PASSWORD_RECOVERY_REQUESTED
    return AuthSecurityEventAction.UNLOCK_REQUESTED


def _confirmation_event_action(purpose: AuthRecoveryPurpose) -> AuthSecurityEventAction:
    if purpose == AuthRecoveryPurpose.PASSWORD_RECOVERY:
        return AuthSecurityEventAction.PASSWORD_RECOVERY_CONFIRMED
    return AuthSecurityEventAction.UNLOCK_CONFIRMED


def _record_token_event(
    session: Session,
    token_row: AuthRecoveryToken,
    action: AuthSecurityEventAction,
    reason: str,
    metadata: AuthRequestMetadata,
    now: datetime,
) -> None:
    record_auth_security_event_by_hash(
        session,
        action=action,
        identifier_digest=token_row.identifier_hash,
        actor_id=None,
        reason=reason,
        metadata=metadata,
        now=now,
    )


def _is_recovery_rate_limited(
    session: Session,
    settings: Settings,
    *,
    identifier: str,
    action: AuthSecurityEventAction,
    now: datetime,
) -> bool:
    window_started_at = now - timedelta(seconds=settings.auth_recovery_window_seconds)
    digest = identifier_hash(settings, identifier)
    events = session.scalars(
        select(AuthSecurityEvent).where(
            AuthSecurityEvent.identifier_hash == digest,
            AuthSecurityEvent.action == action,
            AuthSecurityEvent.reason == "request_accepted",
            AuthSecurityEvent.created_at >= window_started_at,
        )
    ).all()
    return len(events) >= settings.auth_recovery_max_requests


def _token_hash(settings: Settings, token: str) -> str:
    return hmac.new(
        settings.auth_secret.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
