from dataclasses import dataclass
from typing import Literal

from starlette.requests import Request

from oneepis_api.core.access_context_contract import (
    ACCESS_CONTEXT_RUNTIME_STATUS,
    contextual_access_header_names,
)
from oneepis_api.services.auth import AuthenticatedUser


@dataclass(frozen=True)
class AccessContext:
    actor_id: str
    role_names: tuple[str, ...]
    source: Literal["rbac_only"]
    institution_id: str | None = None
    tenant_id: str | None = None
    care_team_id: str | None = None
    access_reason: str | None = None
    break_glass_requested: bool = False
    unsupported_contextual_header_names: tuple[str, ...] = ()
    missing_abac_requirements: tuple[str, ...] = ()
    runtime_abac_enforced: bool = False
    contextual_headers_accepted: bool = False
    break_glass_enabled: bool = False


def build_access_context(
    user: AuthenticatedUser,
    request: Request,
    *,
    abac_requirements: tuple[str, ...],
) -> AccessContext:
    unsupported_header_names = tuple(
        header for header in contextual_access_header_names() if header in request.headers
    )
    return AccessContext(
        actor_id=user.actor_id,
        role_names=tuple(sorted(role.value for role in user.roles)),
        source="rbac_only",
        unsupported_contextual_header_names=unsupported_header_names,
        missing_abac_requirements=abac_requirements,
        runtime_abac_enforced=ACCESS_CONTEXT_RUNTIME_STATUS["runtime_abac_enforced"],
        contextual_headers_accepted=ACCESS_CONTEXT_RUNTIME_STATUS["contextual_headers_accepted"],
        break_glass_enabled=ACCESS_CONTEXT_RUNTIME_STATUS["break_glass_enabled"],
    )
