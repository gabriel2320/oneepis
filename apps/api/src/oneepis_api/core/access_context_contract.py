from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AccessContextRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_phi"]


@dataclass(frozen=True)
class ContextualAccessHeaderContract:
    header: str
    requirement_key: str
    status: Literal["unsupported_until_runtime_abac"]
    audit_metadata: Literal["header_name_only"]
    value_retention: Literal["never_store_header_value"]


@dataclass(frozen=True)
class AccessReasonContract:
    key: str
    label: str
    status: Literal["future_review_required"]
    free_text_retention: Literal["never_store_raw_reason_text"]
    requires_patient_scope: bool
    requires_review: bool


ACCESS_CONTEXT_REQUIREMENTS: tuple[AccessContextRequirement, ...] = (
    AccessContextRequirement(
        key="institution_or_tenant",
        label="Institution or tenant boundary",
        criterion="Clinical access must be bounded by institution or tenant before PHI use.",
        status="required_before_phi",
    ),
    AccessContextRequirement(
        key="care_team_or_service",
        label="Care team or clinical service",
        criterion="Clinical access must evaluate assigned care team or clinical service.",
        status="required_before_phi",
    ),
    AccessContextRequirement(
        key="active_care_relationship_or_access_reason",
        label="Care relationship or access reason",
        criterion=(
            "Clinical access must require an active care relationship or an explicit "
            "auditable access reason."
        ),
        status="required_before_phi",
    ),
    AccessContextRequirement(
        key="audited_break_glass",
        label="Audited break-glass",
        criterion=(
            "Exceptional access must capture actor, reason, timestamp, correlation "
            "and review workflow."
        ),
        status="required_before_phi",
    ),
)


ACCESS_REASON_CONTRACTS: tuple[AccessReasonContract, ...] = (
    AccessReasonContract(
        key="active_care_relationship",
        label="Active care relationship",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_patient_scope=True,
        requires_review=False,
    ),
    AccessReasonContract(
        key="temporary_coverage",
        label="Temporary clinical coverage",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_patient_scope=True,
        requires_review=True,
    ),
    AccessReasonContract(
        key="care_coordination",
        label="Care coordination",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_patient_scope=True,
        requires_review=True,
    ),
    AccessReasonContract(
        key="audit_review",
        label="Audit or compliance review",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_patient_scope=True,
        requires_review=True,
    ),
    AccessReasonContract(
        key="break_glass",
        label="Break-glass exceptional access",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_patient_scope=True,
        requires_review=True,
    ),
)


CONTEXTUAL_ACCESS_HEADER_CONTRACTS: tuple[ContextualAccessHeaderContract, ...] = (
    ContextualAccessHeaderContract(
        header="X-OneEpis-Break-Glass",
        requirement_key="audited_break_glass",
        status="unsupported_until_runtime_abac",
        audit_metadata="header_name_only",
        value_retention="never_store_header_value",
    ),
    ContextualAccessHeaderContract(
        header="X-OneEpis-Access-Reason",
        requirement_key="active_care_relationship_or_access_reason",
        status="unsupported_until_runtime_abac",
        audit_metadata="header_name_only",
        value_retention="never_store_header_value",
    ),
    ContextualAccessHeaderContract(
        header="X-OneEpis-Institution",
        requirement_key="institution_or_tenant",
        status="unsupported_until_runtime_abac",
        audit_metadata="header_name_only",
        value_retention="never_store_header_value",
    ),
    ContextualAccessHeaderContract(
        header="X-OneEpis-Tenant",
        requirement_key="institution_or_tenant",
        status="unsupported_until_runtime_abac",
        audit_metadata="header_name_only",
        value_retention="never_store_header_value",
    ),
    ContextualAccessHeaderContract(
        header="X-OneEpis-Care-Team",
        requirement_key="care_team_or_service",
        status="unsupported_until_runtime_abac",
        audit_metadata="header_name_only",
        value_retention="never_store_header_value",
    ),
)


ACCESS_CONTEXT_RUNTIME_STATUS = {
    "runtime_abac_enforced": False,
    "development_patient_read_enforcement_available": True,
    "development_patient_read_enforcement_scope": "GET /api/v1/patients/{patient_id}",
    "contextual_headers_accepted": False,
    "break_glass_enabled": False,
    "reason": (
        "Contextual ABAC production enforcement is disabled; development-only "
        "patient read enforcement is available behind ONEEPIS_ABAC_ENFORCEMENT_ENABLED."
    ),
}


def access_context_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in ACCESS_CONTEXT_REQUIREMENTS)


def contextual_access_header_names() -> tuple[str, ...]:
    return tuple(contract.header for contract in CONTEXTUAL_ACCESS_HEADER_CONTRACTS)


def access_reason_keys() -> tuple[str, ...]:
    return tuple(contract.key for contract in ACCESS_REASON_CONTRACTS)


def access_reason_audit_metadata(
    reason_key: str,
    *,
    raw_text: str | None = None,
) -> dict[str, object]:
    known_reason_keys = set(access_reason_keys())
    return {
        "access_reason_key": reason_key if reason_key in known_reason_keys else "unknown",
        "access_reason_known": reason_key in known_reason_keys,
        "raw_reason_present": bool((raw_text or "").strip()),
        "raw_reason_retained": False,
    }
