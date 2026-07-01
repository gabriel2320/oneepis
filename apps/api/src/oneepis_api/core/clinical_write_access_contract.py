from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ClinicalWriteAccessRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_runtime_write_abac"]


@dataclass(frozen=True)
class ClinicalWriteSurface:
    key: str
    label: str
    current_guard: Literal["rbac_and_semantic_guard_only"]
    runtime_write_abac: bool


CLINICAL_WRITE_ACCESS_REQUIREMENTS: tuple[ClinicalWriteAccessRequirement, ...] = (
    ClinicalWriteAccessRequirement(
        key="active_care_relationship_or_access_reason",
        label="Active care relationship or access reason",
        criterion=(
            "Clinical writes must require an active care relationship or an "
            "explicit audited access reason."
        ),
        status="required_before_runtime_write_abac",
    ),
    ClinicalWriteAccessRequirement(
        key="actor_write_permission",
        label="Actor write permission",
        criterion="Clinical writes must keep explicit role or permission checks.",
        status="required_before_runtime_write_abac",
    ),
    ClinicalWriteAccessRequirement(
        key="encounter_or_episode_context",
        label="Encounter or episode context",
        criterion=(
            "Clinical writes must bind to the relevant encounter, episode or "
            "patient-scoped clinical context when applicable."
        ),
        status="required_before_runtime_write_abac",
    ),
    ClinicalWriteAccessRequirement(
        key="write_audit_correlation",
        label="Write audit correlation",
        criterion=(
            "Clinical writes must emit minimized audit events with actor, patient, "
            "route and correlation_id."
        ),
        status="required_before_runtime_write_abac",
    ),
    ClinicalWriteAccessRequirement(
        key="reviewed_break_glass",
        label="Reviewed break-glass",
        criterion=(
            "Exceptional write access must require curated reason, expiry, "
            "step-up assurance and post-access review before runtime use."
        ),
        status="required_before_runtime_write_abac",
    ),
    ClinicalWriteAccessRequirement(
        key="human_finalization",
        label="Human finalization",
        criterion=(
            "AI may draft or suggest, but must not autonomously finalize clinical "
            "writes, signatures, prescriptions or executable orders."
        ),
        status="required_before_runtime_write_abac",
    ),
)


CLINICAL_WRITE_SURFACES: tuple[ClinicalWriteSurface, ...] = (
    ClinicalWriteSurface(
        key="clinical_entries",
        label="Clinical entries create/update/delete",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="clinical_events",
        label="Clinical events create/update",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="clinical_orders",
        label="Clinical orders draft/update/cancel",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="vital_signs",
        label="Vital signs create/update/delete",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="clinical_risks",
        label="Clinical risks create/update/delete",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="medications",
        label="Medications create/update/delete",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="allergies",
        label="Allergies create/update/delete",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="active_problems",
        label="Active problems create/update/delete",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="encounters",
        label="Encounters create/update/cancel",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="appointments",
        label="Patient-scoped appointments create/update",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="lab_panels_results",
        label="Lab panels/results create/update",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="hospital_daily_sheets",
        label="Hospital daily sheets create/update/close",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
    ClinicalWriteSurface(
        key="hospital_indications",
        label="Hospital indications create/update/close",
        current_guard="rbac_and_semantic_guard_only",
        runtime_write_abac=False,
    ),
)


CLINICAL_WRITE_ABAC_RUNTIME_STATUS = {
    "clinical_write_relationship_enforced": False,
    "write_break_glass_enabled": False,
    "ai_autonomous_write_finalization_enabled": False,
    "patient_scoped_read_enforcement_available": True,
    "reason": (
        "Clinical write ABAC is a shadow contract only; patient-scoped read "
        "enforcement does not enable runtime write authorization."
    ),
}


def clinical_write_access_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in CLINICAL_WRITE_ACCESS_REQUIREMENTS)


def clinical_write_surface_keys() -> tuple[str, ...]:
    return tuple(surface.key for surface in CLINICAL_WRITE_SURFACES)
