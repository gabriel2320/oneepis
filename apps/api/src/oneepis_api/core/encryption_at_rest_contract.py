from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class EncryptionAtRestRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_production"]


@dataclass(frozen=True)
class ProtectedDataStore:
    key: str
    label: str
    contains_clinical_data: bool
    production_encryption_required: bool


ENCRYPTION_AT_REST_REQUIREMENTS: tuple[EncryptionAtRestRequirement, ...] = (
    EncryptionAtRestRequirement(
        key="database_storage_encryption",
        label="Database storage encryption",
        criterion="Clinical database storage must be encrypted with managed production keys.",
        status="required_before_production",
    ),
    EncryptionAtRestRequirement(
        key="backup_encryption",
        label="Backup encryption",
        criterion="Backups and restore artifacts must be encrypted and access-controlled.",
        status="required_before_production",
    ),
    EncryptionAtRestRequirement(
        key="document_storage_encryption",
        label="Document storage encryption",
        criterion="Future document storage must encrypt attachments, exports and generated files.",
        status="required_before_production",
    ),
    EncryptionAtRestRequirement(
        key="key_ownership_rotation",
        label="Key ownership and rotation",
        criterion="Encryption keys must have owner, rotation cadence and incident procedure.",
        status="required_before_production",
    ),
    EncryptionAtRestRequirement(
        key="restore_path_preserves_encryption",
        label="Restore path preserves encryption",
        criterion="Restore procedures must preserve encryption controls and access boundaries.",
        status="required_before_production",
    ),
)


PROTECTED_DATA_STORES: tuple[ProtectedDataStore, ...] = (
    ProtectedDataStore(
        key="clinical_database",
        label="Clinical PostgreSQL database",
        contains_clinical_data=True,
        production_encryption_required=True,
    ),
    ProtectedDataStore(
        key="audit_events",
        label="Audit event store",
        contains_clinical_data=True,
        production_encryption_required=True,
    ),
    ProtectedDataStore(
        key="database_backups",
        label="Database backups and restore artifacts",
        contains_clinical_data=True,
        production_encryption_required=True,
    ),
    ProtectedDataStore(
        key="document_storage",
        label="Future document and attachment storage",
        contains_clinical_data=True,
        production_encryption_required=True,
    ),
)


def encryption_at_rest_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in ENCRYPTION_AT_REST_REQUIREMENTS)


def protected_data_store_keys() -> tuple[str, ...]:
    return tuple(store.key for store in PROTECTED_DATA_STORES)
