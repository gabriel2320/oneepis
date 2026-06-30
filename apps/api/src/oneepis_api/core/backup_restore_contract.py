from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class BackupRestoreRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_production"]


@dataclass(frozen=True)
class RestoreEvidenceRequirement:
    key: str
    label: str
    must_be_versioned: bool
    must_be_human_reviewed: bool


BACKUP_RESTORE_REQUIREMENTS: tuple[BackupRestoreRequirement, ...] = (
    BackupRestoreRequirement(
        key="automated_backup_schedule",
        label="Automated backup schedule",
        criterion=(
            "Production backups must run automatically with monitored "
            "success/failure signals."
        ),
        status="required_before_production",
    ),
    BackupRestoreRequirement(
        key="defined_rpo_rto",
        label="Defined RPO/RTO",
        criterion="Recovery point and recovery time objectives must be defined and approved.",
        status="required_before_production",
    ),
    BackupRestoreRequirement(
        key="restore_drill",
        label="Restore drill",
        criterion=(
            "Restore must be tested from backup into an isolated environment "
            "before production use."
        ),
        status="required_before_production",
    ),
    BackupRestoreRequirement(
        key="encrypted_backup_storage",
        label="Encrypted backup storage",
        criterion=(
            "Backup artifacts must remain encrypted and access-controlled at "
            "rest and in transit."
        ),
        status="required_before_production",
    ),
    BackupRestoreRequirement(
        key="custody_and_retention",
        label="Custody and retention",
        criterion=(
            "Backup custody, retention period, deletion and legal hold rules "
            "must be documented."
        ),
        status="required_before_production",
    ),
)


RESTORE_EVIDENCE_REQUIREMENTS: tuple[RestoreEvidenceRequirement, ...] = (
    RestoreEvidenceRequirement(
        key="restore_log",
        label="Restore execution log",
        must_be_versioned=True,
        must_be_human_reviewed=True,
    ),
    RestoreEvidenceRequirement(
        key="integrity_check",
        label="Restored database integrity check",
        must_be_versioned=True,
        must_be_human_reviewed=True,
    ),
    RestoreEvidenceRequirement(
        key="access_boundary_check",
        label="Access boundary check after restore",
        must_be_versioned=True,
        must_be_human_reviewed=True,
    ),
)


BACKUP_RESTORE_RUNTIME_STATUS = {
    "production_backup_enabled": False,
    "production_restore_procedure_verified": False,
    "reason": "No automated backup, restore drill, RPO/RTO or custody procedure exists yet.",
}


def backup_restore_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in BACKUP_RESTORE_REQUIREMENTS)


def restore_evidence_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in RESTORE_EVIDENCE_REQUIREMENTS)
