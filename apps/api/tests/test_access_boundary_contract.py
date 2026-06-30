from pathlib import Path

from oneepis_api.core.access_boundary_contract import (
    ACCESS_BOUNDARY_RUNTIME_STATUS,
    ACCESS_BOUNDARY_STORES,
    access_boundary_store_keys,
)
from oneepis_api.models.access_boundary import (
    AccessBoundaryStatus,
    ClinicalInstitution,
    ClinicalTenant,
)


def test_access_boundary_contract_declares_institution_and_tenant_stores() -> None:
    assert access_boundary_store_keys() == ("institution", "tenant")
    assert {store.runtime_enforcement for store in ACCESS_BOUNDARY_STORES} == {"disabled"}
    assert {store.model for store in ACCESS_BOUNDARY_STORES} == {
        "ClinicalInstitution",
        "ClinicalTenant",
    }
    assert {store.table for store in ACCESS_BOUNDARY_STORES} == {
        "clinical_institutions",
        "clinical_tenants",
    }


def test_access_boundary_models_are_bound_to_contract_tables() -> None:
    assert ClinicalInstitution.__tablename__ == "clinical_institutions"
    assert ClinicalTenant.__tablename__ == "clinical_tenants"
    assert [item.value for item in AccessBoundaryStatus] == ["draft", "active", "retired"]
    assert ClinicalInstitution.key.property.columns[0].unique is None
    assert ClinicalTenant.institution_id.property.columns[0].index is True


def test_access_boundary_runtime_does_not_claim_patient_scoping() -> None:
    assert ACCESS_BOUNDARY_RUNTIME_STATUS == {
        "institution_store_available": True,
        "tenant_store_available": True,
        "patient_scoping_enabled": False,
        "abac_runtime_enforced": False,
        "reason": (
            "Institution and tenant stores are model stubs only; no patient access scoping yet."
        ),
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
