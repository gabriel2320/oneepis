from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from oneepis_api.core.config import Settings


class UserRole(StrEnum):
    ADMIN = "admin"
    MEDICO = "medico"
    ENFERMERIA = "enfermeria"
    SOLO_LECTURA = "solo_lectura"
    DEV = "dev"


@dataclass(frozen=True)
class AuthenticatedUser:
    email: str
    name: str
    roles: frozenset[UserRole]
    actor_id: str


@dataclass(frozen=True)
class LocalAuthUser(AuthenticatedUser):
    password: str


class AuthError(ValueError):
    pass


def parse_local_users(settings: Settings) -> dict[str, LocalAuthUser]:
    users: dict[str, LocalAuthUser] = {}
    for raw_item in settings.auth_local_users.split(";"):
        item = raw_item.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split("|")]
        if len(parts) != 4:
            continue
        email, password, name, roles_text = parts
        roles = _parse_roles(roles_text)
        if not email or not password or not roles:
            continue
        normalized_email = email.lower()
        users[normalized_email] = LocalAuthUser(
            email=normalized_email,
            name=name or normalized_email,
            roles=frozenset(roles),
            actor_id=normalized_email,
            password=password,
        )
    return users


def authenticate_local_user(
    settings: Settings,
    email: str,
    password: str,
) -> AuthenticatedUser | None:
    user = parse_local_users(settings).get(email.lower())
    if user is None:
        return None
    if not hmac.compare_digest(user.password, password):
        return None
    return AuthenticatedUser(
        email=user.email,
        name=user.name,
        roles=user.roles,
        actor_id=user.actor_id,
    )


def create_access_token(
    settings: Settings,
    user: AuthenticatedUser,
    now: datetime | None = None,
) -> tuple[str, datetime]:
    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.auth_token_ttl_minutes)
    payload = {
        "sub": user.email,
        "name": user.name,
        "roles": sorted(role.value for role in user.roles),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    encoded_payload = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = _sign(settings.auth_secret, encoded_payload)
    return f"{encoded_payload}.{signature}", expires_at


def verify_access_token(
    settings: Settings,
    token: str,
    now: datetime | None = None,
) -> AuthenticatedUser:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise AuthError("Invalid token format") from exc

    expected_signature = _sign(settings.auth_secret, encoded_payload)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthError("Invalid token signature")

    try:
        payload = json.loads(_b64decode(encoded_payload))
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuthError("Invalid token payload") from exc

    expires_at = int(payload.get("exp", 0))
    current_time = int((now or datetime.now(UTC)).timestamp())
    if expires_at <= current_time:
        raise AuthError("Token expired")

    email = str(payload.get("sub") or "").lower()
    name = str(payload.get("name") or email)
    roles = _parse_roles(payload.get("roles"))
    if not email or not roles:
        raise AuthError("Token missing identity")

    return AuthenticatedUser(
        email=email,
        name=name,
        roles=frozenset(roles),
        actor_id=email,
    )


def create_dev_user(actor_id: str = "dev.system") -> AuthenticatedUser:
    return AuthenticatedUser(
        email=actor_id,
        name=actor_id,
        roles=frozenset({UserRole.DEV, UserRole.ADMIN}),
        actor_id=actor_id,
    )


def _parse_roles(value: Any) -> set[UserRole]:
    if isinstance(value, str):
        raw_roles = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        raw_roles = [str(item).strip() for item in value]
    else:
        raw_roles = []

    roles: set[UserRole] = set()
    for raw_role in raw_roles:
        try:
            roles.add(UserRole(raw_role))
        except ValueError:
            continue
    return roles


def _sign(secret: str, encoded_payload: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64encode(digest)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding).decode("utf-8")
