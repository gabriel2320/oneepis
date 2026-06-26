from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings
from oneepis_api.models.auth_security import AuthRecoveryPurpose, AuthSecurityEventAction
from oneepis_api.services.auth_recovery import AuthRecoveryDispatch
from oneepis_api.services.auth_security import (
    AuthRequestMetadata,
    record_auth_security_event,
)


@dataclass(frozen=True)
class AuthNotificationResult:
    status: str
    link: str | None = None


def dispatch_auth_recovery_notification(
    session: Session,
    settings: Settings,
    *,
    identifier: str,
    dispatch: AuthRecoveryDispatch | None,
    metadata: AuthRequestMetadata,
) -> AuthNotificationResult:
    if dispatch is None:
        return AuthNotificationResult(status="not_created")

    action = _request_event_action(dispatch.purpose)
    if settings.auth_notification_provider == "disabled":
        _record_notification_event(
            session,
            settings,
            identifier=identifier,
            action=action,
            reason="notification_disabled",
            metadata=metadata,
        )
        return AuthNotificationResult(status="disabled")

    if dispatch.purpose == AuthRecoveryPurpose.PASSWORD_RECOVERY:
        _record_notification_event(
            session,
            settings,
            identifier=identifier,
            action=action,
            reason="notification_not_implemented",
            metadata=metadata,
        )
        return AuthNotificationResult(status="not_implemented")

    link = _unlock_link(settings, dispatch.token)
    print(f"OneEpis development unlock link for {identifier}: {link}")
    _record_notification_event(
        session,
        settings,
        identifier=identifier,
        action=action,
        reason="notification_development_logged",
        metadata=metadata,
    )
    return AuthNotificationResult(status="development_logged", link=link)


def _unlock_link(settings: Settings, token: str) -> str:
    base_url = settings.auth_public_web_base_url.rstrip("/")
    query = urlencode({"token": token})
    return f"{base_url}/login/desbloquear/confirmar?{query}"


def _request_event_action(purpose: AuthRecoveryPurpose) -> AuthSecurityEventAction:
    if purpose == AuthRecoveryPurpose.PASSWORD_RECOVERY:
        return AuthSecurityEventAction.PASSWORD_RECOVERY_REQUESTED
    return AuthSecurityEventAction.UNLOCK_REQUESTED


def _record_notification_event(
    session: Session,
    settings: Settings,
    *,
    identifier: str,
    action: AuthSecurityEventAction,
    reason: str,
    metadata: AuthRequestMetadata,
) -> None:
    record_auth_security_event(
        session,
        settings,
        action=action,
        identifier=identifier,
        actor_id=None,
        reason=reason,
        metadata=metadata,
    )
