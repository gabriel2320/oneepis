from __future__ import annotations

from datetime import datetime

from pydantic import Field

from oneepis_api.schemas.common import APIModel
from oneepis_api.services.auth import UserRole


class LoginRequest(APIModel):
    email: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=1, max_length=120)


class AuthRequestAccepted(APIModel):
    accepted: bool = True


class PasswordRecoveryRequest(APIModel):
    email: str = Field(min_length=3, max_length=160)


class UnlockRequest(APIModel):
    email: str = Field(min_length=3, max_length=160)


class UnlockConfirmationRequest(APIModel):
    token: str = Field(min_length=20, max_length=256)


class AuthUserRead(APIModel):
    email: str
    name: str
    roles: list[UserRole]
    actor_id: str


class LoginResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: AuthUserRead
