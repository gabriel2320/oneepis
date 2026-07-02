from oneepis_api.core.clinical_write_access_contract import (
    CLINICAL_WRITE_ABAC_RUNTIME_STATUS,
    CLINICAL_WRITE_ACCESS_REQUIREMENTS,
    CLINICAL_WRITE_SURFACES,
    clinical_write_access_requirement_keys,
    clinical_write_dev_abac_surface_keys,
    clinical_write_surface_keys,
)


def test_clinical_write_contract_tracks_minimum_runtime_requirements() -> None:
    assert clinical_write_access_requirement_keys() == (
        "active_care_relationship_or_access_reason",
        "actor_write_permission",
        "encounter_or_episode_context",
        "write_audit_correlation",
        "reviewed_break_glass",
        "human_finalization",
    )

    assert all(requirement.label for requirement in CLINICAL_WRITE_ACCESS_REQUIREMENTS)
    assert all(
        requirement.criterion for requirement in CLINICAL_WRITE_ACCESS_REQUIREMENTS
    )
    assert {requirement.status for requirement in CLINICAL_WRITE_ACCESS_REQUIREMENTS} == {
        "required_before_runtime_write_abac"
    }


def test_clinical_write_surface_inventory_covers_core_write_families() -> None:
    assert clinical_write_surface_keys() == (
        "clinical_entries",
        "clinical_events",
        "clinical_orders",
        "vital_signs",
        "clinical_risks",
        "medications",
        "allergies",
        "active_problems",
        "encounters",
        "appointments",
        "lab_panels_results",
        "hospital_daily_sheets",
        "hospital_indications",
    )

    assert all(surface.label for surface in CLINICAL_WRITE_SURFACES)
    assert {surface.current_guard for surface in CLINICAL_WRITE_SURFACES} == {
        "rbac_semantic_and_dev_abac_guard",
    }
    assert {surface.runtime_write_abac for surface in CLINICAL_WRITE_SURFACES} == {
        False
    }


def test_clinical_write_contract_does_not_claim_runtime_write_abac() -> None:
    assert CLINICAL_WRITE_ABAC_RUNTIME_STATUS == {
        "clinical_write_relationship_enforced": False,
        "write_break_glass_enabled": False,
        "ai_autonomous_write_finalization_enabled": False,
        "patient_scoped_read_enforcement_available": True,
        "reason": (
            "Clinical write ABAC is a shadow contract only; patient-scoped read "
            "enforcement does not enable runtime write authorization."
        ),
    }


def test_clinical_write_contract_keeps_ai_as_draft_only() -> None:
    human_finalization = {
        requirement.key: requirement
        for requirement in CLINICAL_WRITE_ACCESS_REQUIREMENTS
    }["human_finalization"]

    assert "must not autonomously finalize" in human_finalization.criterion
    assert CLINICAL_WRITE_ABAC_RUNTIME_STATUS[
        "ai_autonomous_write_finalization_enabled"
    ] is False


def test_clinical_write_contract_tracks_dev_only_write_abac_surfaces() -> None:
    surfaces = {surface.key: surface for surface in CLINICAL_WRITE_SURFACES}

    assert surfaces["vital_signs"].dev_write_abac is True
    assert surfaces["vital_signs"].runtime_write_abac is False
    assert surfaces["vital_signs"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["clinical_entries"].dev_write_abac is True
    assert surfaces["clinical_entries"].runtime_write_abac is False
    assert surfaces["clinical_entries"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["clinical_events"].dev_write_abac is True
    assert surfaces["clinical_events"].runtime_write_abac is False
    assert surfaces["clinical_events"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["clinical_orders"].dev_write_abac is True
    assert surfaces["clinical_orders"].runtime_write_abac is False
    assert surfaces["clinical_orders"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["encounters"].dev_write_abac is True
    assert surfaces["encounters"].runtime_write_abac is False
    assert surfaces["encounters"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["clinical_risks"].dev_write_abac is True
    assert surfaces["clinical_risks"].runtime_write_abac is False
    assert surfaces["clinical_risks"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["medications"].dev_write_abac is True
    assert surfaces["medications"].runtime_write_abac is False
    assert surfaces["medications"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["allergies"].dev_write_abac is True
    assert surfaces["allergies"].runtime_write_abac is False
    assert surfaces["allergies"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["active_problems"].dev_write_abac is True
    assert surfaces["active_problems"].runtime_write_abac is False
    assert surfaces["active_problems"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["appointments"].dev_write_abac is True
    assert surfaces["appointments"].runtime_write_abac is False
    assert surfaces["appointments"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["lab_panels_results"].dev_write_abac is True
    assert surfaces["lab_panels_results"].runtime_write_abac is False
    assert surfaces["lab_panels_results"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["hospital_daily_sheets"].dev_write_abac is True
    assert surfaces["hospital_daily_sheets"].runtime_write_abac is False
    assert surfaces["hospital_daily_sheets"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert surfaces["hospital_indications"].dev_write_abac is True
    assert surfaces["hospital_indications"].runtime_write_abac is False
    assert surfaces["hospital_indications"].current_guard == "rbac_semantic_and_dev_abac_guard"
    assert clinical_write_dev_abac_surface_keys() == (
        "clinical_entries",
        "clinical_events",
        "clinical_orders",
        "vital_signs",
        "clinical_risks",
        "medications",
        "allergies",
        "active_problems",
        "encounters",
        "appointments",
        "lab_panels_results",
        "hospital_daily_sheets",
        "hospital_indications",
    )
