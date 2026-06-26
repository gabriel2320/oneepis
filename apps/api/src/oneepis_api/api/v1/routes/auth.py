from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from oneepis_api.api.deps import CurrentUserDep, SettingsDep
from oneepis_api.core.config import Settings
from oneepis_api.db.session import get_session
from oneepis_api.models.auth_security import AuthRecoveryPurpose
from oneepis_api.schemas.auth import (
    AuthRequestAccepted,
    AuthUserRead,
    LoginRequest,
    LoginResponse,
    PasswordRecoveryRequest,
    UnlockConfirmationRequest,
    UnlockRequest,
)
from oneepis_api.services.auth import (
    AuthenticatedUser,
    AuthError,
    authenticate_local_user,
    create_access_token,
    verify_access_token,
)
from oneepis_api.services.auth_notifications import dispatch_auth_recovery_notification
from oneepis_api.services.auth_recovery import consume_recovery_token, create_recovery_request
from oneepis_api.services.auth_security import (
    AuthRequestMetadata,
    is_login_locked,
    record_blocked_login_attempt,
    record_login_failure,
    record_login_success,
)
from oneepis_api.services.auth_sessions import (
    create_auth_session,
    is_auth_session_active,
    revoke_auth_session,
    rotate_auth_session_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[Session, Depends(get_session)]

GENERIC_AUTH_ERROR = "Credenciales invalidas o cuenta no disponible"


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
    response: Response,
) -> LoginResponse:
    metadata = _request_metadata(request)
    if is_login_locked(session, settings, payload.email):
        record_blocked_login_attempt(
            session,
            settings,
            identifier=payload.email,
            metadata=metadata,
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=GENERIC_AUTH_ERROR,
        )

    user = authenticate_local_user(settings, payload.email, payload.password)
    if user is None:
        locked = record_login_failure(
            session,
            settings,
            identifier=payload.email,
            metadata=metadata,
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED if locked else status.HTTP_401_UNAUTHORIZED,
            detail=GENERIC_AUTH_ERROR,
        )

    record_login_success(
        session,
        settings,
        identifier=payload.email,
        actor_id=user.actor_id,
        metadata=metadata,
    )
    session.commit()
    _token_without_session, expires_at = create_access_token(settings, user)
    auth_session = create_auth_session(session, settings, user=user, expires_at=expires_at)
    access_token, expires_at = create_access_token(settings, user, session_id=str(auth_session.id))
    rotate_auth_session_token(
        session,
        settings,
        session_id=str(auth_session.id),
        token=access_token,
        expires_at=expires_at,
    )
    session.commit()
    _set_session_cookie(response, settings, access_token)
    _set_csrf_cookie(response, settings)
    return LoginResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=_read_user(user),
    )


@router.post("/password-recovery-requests", response_model=AuthRequestAccepted, status_code=202)
def request_password_recovery(
    payload: PasswordRecoveryRequest,
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
) -> AuthRequestAccepted:
    metadata = _request_metadata(request)
    dispatch = create_recovery_request(
        session,
        settings,
        identifier=payload.email,
        purpose=AuthRecoveryPurpose.PASSWORD_RECOVERY,
        metadata=metadata,
    )
    dispatch_auth_recovery_notification(
        session,
        settings,
        identifier=payload.email,
        dispatch=dispatch,
        metadata=metadata,
    )
    session.commit()
    return AuthRequestAccepted()


@router.post("/unlock-requests", response_model=AuthRequestAccepted, status_code=202)
def request_unlock(
    payload: UnlockRequest,
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
) -> AuthRequestAccepted:
    metadata = _request_metadata(request)
    dispatch = create_recovery_request(
        session,
        settings,
        identifier=payload.email,
        purpose=AuthRecoveryPurpose.UNLOCK,
        metadata=metadata,
    )
    dispatch_auth_recovery_notification(
        session,
        settings,
        identifier=payload.email,
        dispatch=dispatch,
        metadata=metadata,
    )
    session.commit()
    return AuthRequestAccepted()


@router.post("/unlock-confirmations", response_model=AuthRequestAccepted, status_code=202)
def confirm_unlock(
    payload: UnlockConfirmationRequest,
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
) -> AuthRequestAccepted:
    consume_recovery_token(
        session,
        settings,
        token=payload.token,
        purpose=AuthRecoveryPurpose.UNLOCK,
        metadata=_request_metadata(request),
    )
    session.commit()
    return AuthRequestAccepted()


@router.get("/me", response_model=AuthUserRead)
def get_me(user: CurrentUserDep) -> AuthUserRead:
    return _read_user(user)


@router.post("/refresh", response_model=LoginResponse)
def refresh_session(
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
    response: Response,
) -> LoginResponse:
    token = _extract_request_token(request, settings)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    try:
        user = verify_access_token(settings, token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        ) from exc
    if not is_auth_session_active(session, settings, user.session_id, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )

    access_token, expires_at = create_access_token(settings, user, session_id=user.session_id)
    if user.session_id:
        rotate_auth_session_token(
            session,
            settings,
            session_id=user.session_id,
            token=access_token,
            expires_at=expires_at,
        )
    session.commit()
    _set_session_cookie(response, settings, access_token)
    _set_csrf_cookie(response, settings)
    return LoginResponse(access_token=access_token, expires_at=expires_at, user=_read_user(user))


@router.post("/logout", response_model=AuthRequestAccepted)
def logout(
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
    response: Response,
) -> AuthRequestAccepted:
    _revoke_current_session(session, settings, request)
    session.commit()
    response.delete_cookie(
        settings.auth_session_cookie_name,
        path="/",
        httponly=True,
        secure=_secure_cookie(settings),
        samesite="lax",
    )
    response.delete_cookie(
        settings.auth_csrf_cookie_name,
        path="/",
        secure=_secure_cookie(settings),
        samesite="lax",
    )
    return AuthRequestAccepted()


def _read_user(user: AuthenticatedUser) -> AuthUserRead:
    return AuthUserRead(
        email=user.email,
        name=user.name,
        roles=sorted(user.roles, key=lambda role: role.value),
        actor_id=user.actor_id,
    )


def _request_metadata(request: Request) -> AuthRequestMetadata:
    return AuthRequestMetadata(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _revoke_current_session(session: Session, settings: Settings, request: Request) -> None:
    token = _extract_request_token(request, settings)
    if not token:
        return
    try:
        user = verify_access_token(settings, token)
    except AuthError:
        return
    revoke_auth_session(session, user.session_id)


def _extract_request_token(request: Request, settings: Settings) -> str | None:
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token.strip()
    return request.cookies.get(settings.auth_session_cookie_name)


def _set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.auth_session_cookie_name,
        token,
        max_age=settings.auth_token_ttl_minutes * 60,
        path="/",
        httponly=True,
        secure=_secure_cookie(settings),
        samesite="lax",
    )


def _set_csrf_cookie(response: Response, settings: Settings) -> None:
    response.set_cookie(
        settings.auth_csrf_cookie_name,
        secrets.token_urlsafe(32),
        max_age=settings.auth_token_ttl_minutes * 60,
        path="/",
        httponly=False,
        secure=_secure_cookie(settings),
        samesite="lax",
    )


def _secure_cookie(settings: Settings) -> bool:
    return settings.environment.strip().lower() != "development"
