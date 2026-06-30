from dataclasses import dataclass, replace
from typing import Literal

from starlette.requests import Request

from oneepis_api.core.access_context_contract import (
    ACCESS_CONTEXT_RUNTIME_STATUS,
    contextual_access_header_names,
)
from oneepis_api.services.auth import AuthenticatedUser

PATIENT_SCOPE_DRY_RUN_METADATA_KEYS = (
    "status",
    "matched_care_team_count",
    "actor_active_care_team_count",
    "patient_active_care_team_count",
    "runtime_enforced",
)


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
    patient_scope_dry_run_metadata: dict[str, object] | None = None


@dataclass(frozen=True)
class AccessContextDecision:
    policy: Literal["contextual_abac"]
    runtime_enforced: bool
    allowed: bool
    would_deny_if_enforced: bool
    denial_reasons: tuple[str, ...]
    metadata_retention: Literal["requirement_keys_only"]


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


def attach_patient_scope_dry_run_metadata(
    context: AccessContext,
    metadata: dict[str, object],
) -> AccessContext:
    minimized_metadata = {
        key: metadata[key] for key in PATIENT_SCOPE_DRY_RUN_METADATA_KEYS if key in metadata
    }
    return replace(context, patient_scope_dry_run_metadata=minimized_metadata)


def evaluate_access_context(context: AccessContext) -> AccessContextDecision:
    denial_reasons = tuple(
        f"missing_abac_requirement:{requirement}"
        for requirement in context.missing_abac_requirements
    )
    would_deny_if_enforced = bool(denial_reasons)
    return AccessContextDecision(
        policy="contextual_abac",
        runtime_enforced=context.runtime_abac_enforced,
        allowed=not context.runtime_abac_enforced or not would_deny_if_enforced,
        would_deny_if_enforced=would_deny_if_enforced,
        denial_reasons=denial_reasons,
        metadata_retention="requirement_keys_only",
    )
