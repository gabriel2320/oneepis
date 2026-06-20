from __future__ import annotations

from datetime import datetime

from pydantic import Field

from oneepis_api.schemas.common import APIModel
from oneepis_api.services.auth import UserRole


class LoginRequest(APIModel):
    email: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=1, max_length=120)


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
