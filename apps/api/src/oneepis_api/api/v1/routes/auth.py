from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from oneepis_api.api.deps import CurrentUserDep, SettingsDep
from oneepis_api.schemas.auth import AuthUserRead, LoginRequest, LoginResponse
from oneepis_api.services.auth import (
    AuthenticatedUser,
    authenticate_local_user,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, settings: SettingsDep) -> LoginResponse:
    user = authenticate_local_user(settings, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid local credentials",
        )

    access_token, expires_at = create_access_token(settings, user)
    return LoginResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=_read_user(user),
    )


@router.get("/me", response_model=AuthUserRead)
def get_me(user: CurrentUserDep) -> AuthUserRead:
    return _read_user(user)


def _read_user(user: AuthenticatedUser) -> AuthUserRead:
    return AuthUserRead(
        email=user.email,
        name=user.name,
        roles=sorted(user.roles, key=lambda role: role.value),
        actor_id=user.actor_id,
    )
