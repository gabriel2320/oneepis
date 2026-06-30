from oneepis_api.core.encryption_at_rest_contract import (
    ENCRYPTION_AT_REST_REQUIREMENTS,
    PROTECTED_DATA_STORES,
    encryption_at_rest_requirement_keys,
    protected_data_store_keys,
)


def test_encryption_at_rest_contract_tracks_minimum_requirements() -> None:
    assert encryption_at_rest_requirement_keys() == (
        "database_storage_encryption",
        "backup_encryption",
        "document_storage_encryption",
        "key_ownership_rotation",
        "restore_path_preserves_encryption",
    )

    assert all(requirement.label for requirement in ENCRYPTION_AT_REST_REQUIREMENTS)
    assert all(requirement.criterion for requirement in ENCRYPTION_AT_REST_REQUIREMENTS)
    assert {requirement.status for requirement in ENCRYPTION_AT_REST_REQUIREMENTS} == {
        "required_before_production"
    }


def test_protected_data_store_inventory_is_explicit() -> None:
    assert protected_data_store_keys() == (
        "clinical_database",
        "audit_events",
        "database_backups",
        "document_storage",
    )

    assert all(store.contains_clinical_data for store in PROTECTED_DATA_STORES)
    assert all(store.production_encryption_required for store in PROTECTED_DATA_STORES)


def test_encryption_contract_does_not_claim_runtime_encryption() -> None:
    criteria = " ".join(requirement.criterion for requirement in ENCRYPTION_AT_REST_REQUIREMENTS)

    assert "must" in criteria
    assert "required_before_production" in {
        requirement.status for requirement in ENCRYPTION_AT_REST_REQUIREMENTS
    }
