from pathlib import Path

from oneepis_api.core.access_boundary_contract import (
    ACCESS_BOUNDARY_RUNTIME_STATUS,
    ACCESS_BOUNDARY_STORES,
    access_boundary_store_keys,
)
from oneepis_api.models.access_boundary import (
    AccessBoundaryStatus,
    CareTeam,
    ClinicalInstitution,
    ClinicalService,
    ClinicalTenant,
    PatientCareTeamRelationship,
)


def test_access_boundary_contract_declares_institution_and_tenant_stores() -> None:
    assert access_boundary_store_keys() == (
        "institution",
        "tenant",
        "clinical_service",
        "care_team",
        "patient_care_team_relationship",
    )
    assert {store.runtime_enforcement for store in ACCESS_BOUNDARY_STORES} == {"disabled"}
    assert {store.model for store in ACCESS_BOUNDARY_STORES} == {
        "CareTeam",
        "ClinicalInstitution",
        "ClinicalService",
        "ClinicalTenant",
        "PatientCareTeamRelationship",
    }
    assert {store.table for store in ACCESS_BOUNDARY_STORES} == {
        "care_teams",
        "clinical_institutions",
        "clinical_services",
        "clinical_tenants",
        "patient_care_team_relationships",
    }


def test_access_boundary_models_are_bound_to_contract_tables() -> None:
    assert ClinicalInstitution.__tablename__ == "clinical_institutions"
    assert ClinicalTenant.__tablename__ == "clinical_tenants"
    assert [item.value for item in AccessBoundaryStatus] == ["draft", "active", "retired"]
    assert ClinicalInstitution.key.property.columns[0].unique is None
    assert ClinicalTenant.institution_id.property.columns[0].index is True
    assert ClinicalService.__tablename__ == "clinical_services"
    assert CareTeam.__tablename__ == "care_teams"
    assert PatientCareTeamRelationship.__tablename__ == "patient_care_team_relationships"
    assert ClinicalService.tenant_id.property.columns[0].index is True
    assert CareTeam.service_id.property.columns[0].index is True
    assert PatientCareTeamRelationship.patient_id.property.columns[0].index is True
    assert PatientCareTeamRelationship.care_team_id.property.columns[0].index is True


def test_access_boundary_runtime_does_not_claim_patient_scoping() -> None:
    assert ACCESS_BOUNDARY_RUNTIME_STATUS == {
        "institution_store_available": True,
        "tenant_store_available": True,
        "clinical_service_store_available": True,
        "care_team_store_available": True,
        "patient_care_team_relationship_store_available": True,
        "patient_scoping_enabled": False,
        "abac_runtime_enforced": False,
        "reason": "Access boundary stores are model stubs only; no patient access scoping yet.",
    }


def test_access_boundary_migration_is_isolated_from_patient_table() -> None:
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "202606200022_access_boundaries.py"
    ).read_text(encoding="utf-8")

    assert "clinical_institutions" in migration
    assert "clinical_tenants" in migration
    assert "patients" not in migration
    assert "patient_id" not in migration


def test_patient_care_team_relationship_migration_keeps_abac_runtime_disabled() -> None:
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "202606200024_patient_care_team_relationships.py"
    ).read_text(encoding="utf-8")

    assert "patient_care_team_relationships" in migration
    assert "patients.id" in migration
    assert "care_teams.id" in migration
    assert "uq_patient_care_team_relationship" in migration
    assert "ACCESS_CONTEXT_RUNTIME_STATUS" not in migration
    assert "abac_runtime_enforced" not in migration


def test_care_team_service_migration_is_isolated_from_patient_table() -> None:
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "202606200023_care_team_service_boundaries.py"
    ).read_text(encoding="utf-8")

    assert "clinical_services" in migration
    assert "care_teams" in migration
    assert "clinical_tenants" in migration
    assert "patients" not in migration
    assert "patient_id" not in migration
