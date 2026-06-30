from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ClinicalGovernanceRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_phi_or_clinical_operation"]


@dataclass(frozen=True)
class ClinicalClaimBoundary:
    key: str
    claim: str
    allowed_now: bool
    reason: str


CLINICAL_GOVERNANCE_REQUIREMENTS: tuple[ClinicalGovernanceRequirement, ...] = (
    ClinicalGovernanceRequirement(
        key="named_clinical_owner",
        label="Named clinical owner",
        criterion=(
            "A qualified clinical owner must be named for safety scope, workflow "
            "approval and clinical risk acceptance."
        ),
        status="required_before_phi_or_clinical_operation",
    ),
    ClinicalGovernanceRequirement(
        key="legal_review",
        label="Legal review",
        criterion=(
            "Legal review must approve intended use, disclaimers, data handling, "
            "retention and jurisdictional obligations."
        ),
        status="required_before_phi_or_clinical_operation",
    ),
    ClinicalGovernanceRequirement(
        key="allowed_use_policy",
        label="Allowed use policy",
        criterion=(
            "Permitted workflows, excluded workflows and user responsibilities "
            "must be documented and approved."
        ),
        status="required_before_phi_or_clinical_operation",
    ),
    ClinicalGovernanceRequirement(
        key="clinical_safety_review",
        label="Clinical safety review",
        criterion=(
            "Clinical risks, human confirmation points, escalation paths and "
            "known limitations must be reviewed before real use."
        ),
        status="required_before_phi_or_clinical_operation",
    ),
    ClinicalGovernanceRequirement(
        key="operational_approval_record",
        label="Operational approval record",
        criterion=(
            "A dated approval record must identify environment, scope, owner, "
            "accepted residual risk and rollback/incident path."
        ),
        status="required_before_phi_or_clinical_operation",
    ),
)


CLINICAL_CLAIM_BOUNDARIES: tuple[ClinicalClaimBoundary, ...] = (
    ClinicalClaimBoundary(
        key="production_healthcare_use",
        claim="Ready for healthcare production use",
        allowed_now=False,
        reason="No clinical owner, legal review or operational approval exists.",
    ),
    ClinicalClaimBoundary(
        key="certified_clinical_software",
        claim="Certified clinical or medical device software",
        allowed_now=False,
        reason="No certification scope, regulator review or legal approval exists.",
    ),
    ClinicalClaimBoundary(
        key="real_phi_storage",
        claim="Approved to store real PHI",
        allowed_now=False,
        reason="No PHI approval, ABAC runtime, productive auth or encryption runtime exists.",
    ),
    ClinicalClaimBoundary(
        key="autonomous_clinical_decision",
        claim="Autonomous clinical decision-making",
        allowed_now=False,
        reason="OneEpis requires human review and does not replace clinical judgment.",
    ),
)


CLINICAL_GOVERNANCE_RUNTIME_STATUS = {
    "clinical_owner_approved": False,
    "legal_review_approved": False,
    "operational_use_approved": False,
    "real_phi_use_approved": False,
    "reason": (
        "Clinical governance is an executable no-production contract only; "
        "human approval records are future work."
    ),
}


def clinical_governance_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in CLINICAL_GOVERNANCE_REQUIREMENTS)


def clinical_claim_boundary_keys() -> tuple[str, ...]:
    return tuple(boundary.key for boundary in CLINICAL_CLAIM_BOUNDARIES)
