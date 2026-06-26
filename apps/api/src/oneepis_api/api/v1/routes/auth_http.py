from __future__ import annotations

import secrets

from fastapi import Request, Response
from sqlalchemy.orm import Session

from oneepis_api.core.config import Settings
from oneepis_api.schemas.auth import AuthUserRead
from oneepis_api.services.auth import AuthenticatedUser, AuthError, verify_access_token
from oneepis_api.services.auth_security import AuthRequestMetadata
from oneepis_api.services.auth_sessions import revoke_auth_session

GENERIC_AUTH_ERROR = "Credenciales invalidas o cuenta no disponible"


def read_auth_user(user: AuthenticatedUser) -> AuthUserRead:
    return AuthUserRead(
        email=user.email,
        name=user.name,
        roles=sorted(user.roles, key=lambda role: role.value),
        actor_id=user.actor_id,
    )


def request_metadata(request: Request) -> AuthRequestMetadata:
    return AuthRequestMetadata(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def revoke_current_session(session: Session, settings: Settings, request: Request) -> None:
    token = extract_request_token(request, settings)
    if not token:
        return
    try:
        user = verify_access_token(settings, token)
    except AuthError:
        return
    revoke_auth_session(session, user.session_id)


def extract_request_token(request: Request, settings: Settings) -> str | None:
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token.strip()
    return request.cookies.get(settings.auth_session_cookie_name)


def set_auth_cookies(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.auth_session_cookie_name,
        token,
        max_age=settings.auth_token_ttl_minutes * 60,
        path="/",
        httponly=True,
        secure=secure_cookie(settings),
        samesite="lax",
    )
    response.set_cookie(
        settings.auth_csrf_cookie_name,
        secrets.token_urlsafe(32),
        max_age=settings.auth_token_ttl_minutes * 60,
        path="/",
        httponly=False,
        secure=secure_cookie(settings),
        samesite="lax",
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        settings.auth_session_cookie_name,
        path="/",
        httponly=True,
        secure=secure_cookie(settings),
        samesite="lax",
    )
    response.delete_cookie(
        settings.auth_csrf_cookie_name,
        path="/",
        secure=secure_cookie(settings),
        samesite="lax",
    )


def secure_cookie(settings: Settings) -> bool:
    return settings.environment.strip().lower() != "development"
