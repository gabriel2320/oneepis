from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class NoProductionSecurityGate:
    gate_id: str
    label: str
    contract_module: str
    checklist_status: Literal["pending"]
    runtime_enabled: bool
    evidence_required: tuple[str, ...]


NO_PRODUCTION_SECURITY_GATES: tuple[NoProductionSecurityGate, ...] = (
    NoProductionSecurityGate(
        gate_id="NOPROD-SEC-001",
        label="Formal secret management",
        contract_module="oneepis_api.core.secret_management_contract",
        checklist_status="pending",
        runtime_enabled=False,
        evidence_required=(
            "external_secret_store",
            "secret_owners",
            "rotation_policy",
            "incident_procedure",
            "environment_isolation",
        ),
    ),
    NoProductionSecurityGate(
        gate_id="NOPROD-SEC-002",
        label="Encryption at rest",
        contract_module="oneepis_api.core.encryption_at_rest_contract",
        checklist_status="pending",
        runtime_enabled=False,
        evidence_required=(
            "database_storage_encryption",
            "backup_encryption",
            "document_storage_encryption",
            "key_ownership_rotation",
            "restore_path_preserves_encryption",
        ),
    ),
    NoProductionSecurityGate(
        gate_id="NOPROD-SEC-003",
        label="Backup and restore",
        contract_module="oneepis_api.core.backup_restore_contract",
        checklist_status="pending",
        runtime_enabled=False,
        evidence_required=(
            "automated_backup_schedule",
            "defined_rpo_rto",
            "restore_drill",
            "encrypted_backup_storage",
            "custody_and_retention",
        ),
    ),
)


NO_PRODUCTION_SECURITY_RUNTIME_STATUS = {
    "secret_store_configured": False,
    "encryption_at_rest_verified": False,
    "backup_restore_drill_verified": False,
    "real_phi_allowed": False,
    "reason": (
        "SEC-001/002/003 are contractual gates only; no production secret store, "
        "encryption verification or restore drill has been approved."
    ),
}


def no_production_security_gate_ids() -> tuple[str, ...]:
    return tuple(gate.gate_id for gate in NO_PRODUCTION_SECURITY_GATES)


def no_production_security_contract_modules() -> tuple[str, ...]:
    return tuple(gate.contract_module for gate in NO_PRODUCTION_SECURITY_GATES)
