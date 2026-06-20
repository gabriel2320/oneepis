from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from oneepis_api.core.config import Settings, get_settings
from oneepis_api.services.auth import (
    AuthenticatedUser,
    AuthError,
    UserRole,
    create_dev_user,
    verify_access_token,
)

SettingsDep = Annotated[Settings, Depends(get_settings)]
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]
ActorHeader = Annotated[
    str | None,
    Header(alias="X-OneEpis-Actor", min_length=1, max_length=120),
]


def get_current_user(
    settings: SettingsDep,
    authorization: AuthorizationHeader = None,
    actor: ActorHeader = None,
) -> AuthenticatedUser:
    if not settings.auth_enabled:
        return create_dev_user(actor or "dev.system")

    token = _extract_bearer_token(authorization)
    if token:
        try:
            return verify_access_token(settings, token)
        except AuthError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
            ) from exc

    if settings.auth_allow_dev_actor_header and actor:
        return create_dev_user(actor)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    allowed = set(allowed_roles)

    def dependency(user: CurrentUserDep) -> AuthenticatedUser:
        if UserRole.ADMIN in user.roles or user.roles.intersection(allowed):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role for this action",
        )

    return dependency


def require_patient_read_access(user: CurrentUserDep) -> AuthenticatedUser:
    return require_roles(
        UserRole.ADMIN,
        UserRole.MEDICO,
        UserRole.ENFERMERIA,
        UserRole.SOLO_LECTURA,
        UserRole.DEV,
    )(user)


def require_clinical_write_access(user: CurrentUserDep) -> AuthenticatedUser:
    return require_roles(
        UserRole.ADMIN,
        UserRole.MEDICO,
        UserRole.ENFERMERIA,
        UserRole.DEV,
    )(user)


def require_ai_access(user: CurrentUserDep) -> AuthenticatedUser:
    return require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.DEV)(user)


ReadAccessDep = Annotated[AuthenticatedUser, Depends(require_patient_read_access)]
WriteAccessDep = Annotated[AuthenticatedUser, Depends(require_clinical_write_access)]
AiAccessDep = Annotated[AuthenticatedUser, Depends(require_ai_access)]


def get_write_actor(user: WriteAccessDep) -> str:
    return user.actor_id


ActorDep = Annotated[str, Depends(get_write_actor)]


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()
