from oneepis_api.core.backup_restore_contract import (
    BACKUP_RESTORE_REQUIREMENTS,
    BACKUP_RESTORE_RUNTIME_STATUS,
    RESTORE_EVIDENCE_REQUIREMENTS,
    backup_restore_requirement_keys,
    restore_evidence_requirement_keys,
)
from oneepis_api.core.encryption_at_rest_contract import protected_data_store_keys


def test_backup_restore_contract_tracks_minimum_requirements() -> None:
    assert backup_restore_requirement_keys() == (
        "automated_backup_schedule",
        "defined_rpo_rto",
        "restore_drill",
        "encrypted_backup_storage",
        "custody_and_retention",
    )

    assert all(requirement.label for requirement in BACKUP_RESTORE_REQUIREMENTS)
    assert all(requirement.criterion for requirement in BACKUP_RESTORE_REQUIREMENTS)
    assert {requirement.status for requirement in BACKUP_RESTORE_REQUIREMENTS} == {
        "required_before_production"
    }


def test_restore_evidence_requirements_are_reviewable_and_versioned() -> None:
    assert restore_evidence_requirement_keys() == (
        "restore_log",
        "integrity_check",
        "access_boundary_check",
    )

    assert all(requirement.must_be_versioned for requirement in RESTORE_EVIDENCE_REQUIREMENTS)
    assert all(
        requirement.must_be_human_reviewed for requirement in RESTORE_EVIDENCE_REQUIREMENTS
    )


def test_backup_contract_covers_encrypted_database_backups() -> None:
    assert "database_backups" in protected_data_store_keys()
    assert BACKUP_RESTORE_RUNTIME_STATUS == {
        "production_backup_enabled": False,
        "production_restore_procedure_verified": False,
        "reason": "No automated backup, restore drill, RPO/RTO or custody procedure exists yet.",
    }
