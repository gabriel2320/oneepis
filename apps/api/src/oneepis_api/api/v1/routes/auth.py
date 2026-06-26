from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from oneepis_api.api.deps import CurrentUserDep, SettingsDep
from oneepis_api.api.v1.routes.auth_http import (
    GENERIC_AUTH_ERROR,
    clear_auth_cookies,
    extract_request_token,
    read_auth_user,
    request_metadata,
    revoke_current_session,
    set_auth_cookies,
)
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
    AuthError,
    authenticate_local_user,
    create_access_token,
    verify_access_token,
)
from oneepis_api.services.auth_notifications import dispatch_auth_recovery_notification
from oneepis_api.services.auth_recovery import consume_recovery_token, create_recovery_request
from oneepis_api.services.auth_security import (
    is_login_locked,
    record_blocked_login_attempt,
    record_login_failure,
    record_login_success,
)
from oneepis_api.services.auth_sessions import (
    create_auth_session,
    is_auth_session_active,
    rotate_auth_session_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
    response: Response,
) -> LoginResponse:
    metadata = request_metadata(request)
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
    set_auth_cookies(response, settings, access_token)
    return LoginResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=read_auth_user(user),
    )


@router.post("/password-recovery-requests", response_model=AuthRequestAccepted, status_code=202)
def request_password_recovery(
    payload: PasswordRecoveryRequest,
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
) -> AuthRequestAccepted:
    metadata = request_metadata(request)
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
    metadata = request_metadata(request)
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
        metadata=request_metadata(request),
    )
    session.commit()
    return AuthRequestAccepted()


@router.get("/me", response_model=AuthUserRead)
def get_me(user: CurrentUserDep) -> AuthUserRead:
    return read_auth_user(user)


@router.post("/refresh", response_model=LoginResponse)
def refresh_session(
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
    response: Response,
) -> LoginResponse:
    token = extract_request_token(request, settings)
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
    set_auth_cookies(response, settings, access_token)
    return LoginResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=read_auth_user(user),
    )


@router.post("/logout", response_model=AuthRequestAccepted)
def logout(
    settings: SettingsDep,
    session: SessionDep,
    request: Request,
    response: Response,
) -> AuthRequestAccepted:
    revoke_current_session(session, settings, request)
    session.commit()
    clear_auth_cookies(response, settings)
    return AuthRequestAccepted()
