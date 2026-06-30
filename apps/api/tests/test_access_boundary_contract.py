from pathlib import Path

from oneepis_api.core.access_boundary_contract import (
    ACCESS_BOUNDARY_REASON_FIELDS,
    ACCESS_BOUNDARY_RUNTIME_STATUS,
    ACCESS_BOUNDARY_STORES,
    access_boundary_reason_audit_metadata,
    access_boundary_store_keys,
)
from oneepis_api.models.access_boundary import (
    AccessBoundaryStatus,
    ActorCareTeamMembership,
    BreakGlassAccessRequest,
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
        "actor_care_team_membership",
        "break_glass_access_request",
    )
    assert {store.runtime_enforcement for store in ACCESS_BOUNDARY_STORES} == {"disabled"}
    assert {store.model for store in ACCESS_BOUNDARY_STORES} == {
        "ActorCareTeamMembership",
        "BreakGlassAccessRequest",
        "CareTeam",
        "ClinicalInstitution",
        "ClinicalService",
        "ClinicalTenant",
        "PatientCareTeamRelationship",
    }
    assert {store.table for store in ACCESS_BOUNDARY_STORES} == {
        "actor_care_team_memberships",
        "break_glass_access_requests",
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
    assert ActorCareTeamMembership.__tablename__ == "actor_care_team_memberships"
    assert BreakGlassAccessRequest.__tablename__ == "break_glass_access_requests"
    assert ClinicalService.tenant_id.property.columns[0].index is True
    assert CareTeam.service_id.property.columns[0].index is True
    assert PatientCareTeamRelationship.patient_id.property.columns[0].index is True
    assert PatientCareTeamRelationship.care_team_id.property.columns[0].index is True
    assert ActorCareTeamMembership.actor_id.property.columns[0].index is True
    assert ActorCareTeamMembership.care_team_id.property.columns[0].index is True
    assert BreakGlassAccessRequest.actor_id.property.columns[0].index is True
    assert BreakGlassAccessRequest.patient_id.property.columns[0].index is True
    assert BreakGlassAccessRequest.correlation_id.property.columns[0].index is True


def test_access_boundary_runtime_does_not_claim_patient_scoping() -> None:
    assert ACCESS_BOUNDARY_RUNTIME_STATUS == {
        "institution_store_available": True,
        "tenant_store_available": True,
        "clinical_service_store_available": True,
        "care_team_store_available": True,
        "patient_care_team_relationship_store_available": True,
        "actor_care_team_membership_store_available": True,
        "break_glass_access_request_store_available": True,
        "patient_scoping_enabled": False,
        "abac_runtime_enforced": False,
        "reason": "Access boundary stores are model stubs only; no patient access scoping yet.",
    }


def test_access_boundary_reason_fields_are_phi_adjacent_minimized_metadata() -> None:
    assert ACCESS_BOUNDARY_REASON_FIELDS == ("membership_reason", "relationship_reason")
    assert access_boundary_reason_audit_metadata(None) == {
        "reason_present": False,
        "reason_length_bucket": "none",
        "raw_reason_retained": False,
    }
    assert access_boundary_reason_audit_metadata("Cobertura temporal") == {
        "reason_present": True,
        "reason_length_bucket": "1_40",
        "raw_reason_retained": False,
    }
    assert access_boundary_reason_audit_metadata("x" * 80) == {
        "reason_present": True,
        "reason_length_bucket": "41_120",
        "raw_reason_retained": False,
    }
    sensitive_reason = "texto libre con PHI que no debe quedar en auditoria"
    metadata = access_boundary_reason_audit_metadata(sensitive_reason)
    assert sensitive_reason not in repr(metadata)


def test_runtime_audit_code_does_not_reference_access_boundary_reason_text() -> None:
    api_source_root = Path(__file__).parents[1] / "src" / "oneepis_api"
    scanned_paths = [
        *sorted((api_source_root / "api" / "v1" / "routes").glob("*.py")),
        *sorted((api_source_root / "services").glob("*.py")),
    ]
    blocked_fields = set(ACCESS_BOUNDARY_REASON_FIELDS)
    offenders: list[str] = []
    for path in scanned_paths:
        text = path.read_text(encoding="utf-8")
        for field in blocked_fields:
            if field in text:
                offenders.append(f"{path.relative_to(api_source_root)}:{field}")

    assert offenders == []


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


def test_actor_care_team_membership_migration_avoids_user_store_claim() -> None:
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "202606200025_actor_care_team_memberships.py"
    ).read_text(encoding="utf-8")

    assert "actor_care_team_memberships" in migration
    assert "actor_id" in migration
    assert "care_teams.id" in migration
    assert "uq_actor_care_team_membership" in migration
    assert "auth_users" not in migration
    assert "users.id" not in migration
    assert "abac_runtime_enforced" not in migration


def test_break_glass_access_request_migration_keeps_runtime_disabled() -> None:
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "202606200026_break_glass_access_requests.py"
    ).read_text(encoding="utf-8")

    assert "break_glass_access_requests" in migration
    assert "actor_id" in migration
    assert "patient_id" in migration
    assert "correlation_id" in migration
    assert "reason_code" in migration
    assert "patients.id" in migration
    assert "X-OneEpis-Break-Glass" not in migration
    assert "break_glass_enabled" not in migration
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
