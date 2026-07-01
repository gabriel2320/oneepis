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


@dataclass(frozen=True)
class BreakGlassReasonCodeContract:
    key: str
    label: str
    status: Literal["future_review_required"]
    free_text_retention: Literal["never_store_raw_reason_text"]
    requires_expiration: bool
    requires_mfa_step_up: bool
    requires_post_access_review: bool
    audit_severity: Literal["high"]


@dataclass(frozen=True)
class BreakGlassReviewControl:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_runtime_break_glass"]


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


BREAK_GLASS_REASON_CODES: tuple[BreakGlassReasonCodeContract, ...] = (
    BreakGlassReasonCodeContract(
        key="urgent_patient_safety",
        label="Urgent patient safety",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_expiration=True,
        requires_mfa_step_up=True,
        requires_post_access_review=True,
        audit_severity="high",
    ),
    BreakGlassReasonCodeContract(
        key="temporary_clinical_coverage",
        label="Temporary clinical coverage",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_expiration=True,
        requires_mfa_step_up=True,
        requires_post_access_review=True,
        audit_severity="high",
    ),
    BreakGlassReasonCodeContract(
        key="audit_or_compliance_access",
        label="Audit or compliance access",
        status="future_review_required",
        free_text_retention="never_store_raw_reason_text",
        requires_expiration=True,
        requires_mfa_step_up=True,
        requires_post_access_review=True,
        audit_severity="high",
    ),
)


BREAK_GLASS_REVIEW_CONTROLS: tuple[BreakGlassReviewControl, ...] = (
    BreakGlassReviewControl(
        key="curated_reason_code",
        label="Curated reason code",
        criterion="Break-glass must use a reviewed reason code, not raw free text.",
        status="required_before_runtime_break_glass",
    ),
    BreakGlassReviewControl(
        key="bounded_expiration",
        label="Bounded expiration",
        criterion="Every break-glass request must expire automatically.",
        status="required_before_runtime_break_glass",
    ),
    BreakGlassReviewControl(
        key="future_mfa_step_up",
        label="Future MFA step-up",
        criterion="Runtime break-glass must require MFA or equivalent assurance.",
        status="required_before_runtime_break_glass",
    ),
    BreakGlassReviewControl(
        key="post_access_review",
        label="Post-access review",
        criterion="Exceptional access must enter a human review workflow after use.",
        status="required_before_runtime_break_glass",
    ),
    BreakGlassReviewControl(
        key="high_severity_audit",
        label="High-severity audit",
        criterion="Break-glass activity must emit minimized high-severity audit events.",
        status="required_before_runtime_break_glass",
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
    "break_glass_review_runtime_enabled": False,
    "break_glass_mfa_step_up_enabled": False,
    "break_glass_post_access_review_enabled": False,
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


def break_glass_reason_code_keys() -> tuple[str, ...]:
    return tuple(contract.key for contract in BREAK_GLASS_REASON_CODES)


def break_glass_review_control_keys() -> tuple[str, ...]:
    return tuple(control.key for control in BREAK_GLASS_REVIEW_CONTROLS)


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
