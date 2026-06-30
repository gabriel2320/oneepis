from oneepis_api.core.clinical_governance_contract import (
    CLINICAL_CLAIM_BOUNDARIES,
    CLINICAL_GOVERNANCE_REQUIREMENTS,
    CLINICAL_GOVERNANCE_RUNTIME_STATUS,
    clinical_claim_boundary_keys,
    clinical_governance_requirement_keys,
)


def test_clinical_governance_contract_tracks_minimum_requirements() -> None:
    assert clinical_governance_requirement_keys() == (
        "named_clinical_owner",
        "legal_review",
        "allowed_use_policy",
        "clinical_safety_review",
        "operational_approval_record",
    )

    assert all(requirement.label for requirement in CLINICAL_GOVERNANCE_REQUIREMENTS)
    assert all(requirement.criterion for requirement in CLINICAL_GOVERNANCE_REQUIREMENTS)
    assert {requirement.status for requirement in CLINICAL_GOVERNANCE_REQUIREMENTS} == {
        "required_before_phi_or_clinical_operation"
    }


def test_clinical_claim_boundaries_block_production_claims() -> None:
    assert clinical_claim_boundary_keys() == (
        "production_healthcare_use",
        "certified_clinical_software",
        "real_phi_storage",
        "autonomous_clinical_decision",
    )

    assert all(not boundary.allowed_now for boundary in CLINICAL_CLAIM_BOUNDARIES)
    assert all(boundary.claim for boundary in CLINICAL_CLAIM_BOUNDARIES)
    assert all(boundary.reason for boundary in CLINICAL_CLAIM_BOUNDARIES)


def test_clinical_governance_contract_does_not_claim_operational_approval() -> None:
    assert CLINICAL_GOVERNANCE_RUNTIME_STATUS == {
        "clinical_owner_approved": False,
        "legal_review_approved": False,
        "operational_use_approved": False,
        "real_phi_use_approved": False,
        "reason": (
            "Clinical governance is an executable no-production contract only; "
            "human approval records are future work."
        ),
    }
