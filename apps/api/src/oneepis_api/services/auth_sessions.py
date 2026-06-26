from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings
from oneepis_api.models.auth_security import AuthSession
from oneepis_api.services.auth import AuthenticatedUser
from oneepis_api.services.auth_security import as_aware_datetime, identifier_hash


def create_auth_session(
    session: Session,
    settings: Settings,
    *,
    user: AuthenticatedUser,
    expires_at: datetime,
) -> AuthSession:
    auth_session = AuthSession(
        actor_id=user.actor_id,
        identifier_hash=identifier_hash(settings, user.email),
        expires_at=expires_at,
    )
    session.add(auth_session)
    session.flush()
    return auth_session


def is_auth_session_active(
    session: Session,
    settings: Settings,
    session_id: str | None,
    token: str | None = None,
    now: datetime | None = None,
) -> bool:
    if not session_id:
        return True
    auth_session = _get_auth_session(session, session_id)
    if auth_session is None or auth_session.revoked_at is not None:
        return False
    if auth_session.token_hash and token:
        if not hmac.compare_digest(auth_session.token_hash, token_hash(settings, token)):
            return False
    current_time = now or datetime.now(UTC)
    return as_aware_datetime(auth_session.expires_at) > current_time


def revoke_auth_session(
    session: Session,
    session_id: str | None,
    now: datetime | None = None,
) -> None:
    if not session_id:
        return
    auth_session = _get_auth_session(session, session_id)
    if auth_session is None or auth_session.revoked_at is not None:
        return
    auth_session.revoked_at = now or datetime.now(UTC)


def rotate_auth_session_token(
    session: Session,
    settings: Settings,
    *,
    session_id: str,
    token: str,
    expires_at: datetime,
) -> bool:
    auth_session = _get_auth_session(session, session_id)
    if auth_session is None or auth_session.revoked_at is not None:
        return False
    auth_session.token_hash = token_hash(settings, token)
    auth_session.expires_at = expires_at
    return True


def token_hash(settings: Settings, token: str) -> str:
    return hmac.new(
        settings.auth_secret.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _get_auth_session(session: Session, session_id: str) -> AuthSession | None:
    try:
        parsed_session_id = uuid.UUID(session_id)
    except ValueError:
        return None
    return session.get(AuthSession, parsed_session_id)
