import importlib

from oneepis_api.core.backup_restore_contract import backup_restore_requirement_keys
from oneepis_api.core.encryption_at_rest_contract import encryption_at_rest_requirement_keys
from oneepis_api.core.no_production_security_contract import (
    NO_PRODUCTION_SECURITY_GATES,
    NO_PRODUCTION_SECURITY_RUNTIME_STATUS,
    no_production_security_contract_modules,
    no_production_security_gate_ids,
)
from oneepis_api.core.secret_management_contract import secret_management_requirement_keys


def test_no_production_security_contract_tracks_sec_001_002_003() -> None:
    assert no_production_security_gate_ids() == (
        "NOPROD-SEC-001",
        "NOPROD-SEC-002",
        "NOPROD-SEC-003",
    )
    assert all(gate.label for gate in NO_PRODUCTION_SECURITY_GATES)
    assert {gate.checklist_status for gate in NO_PRODUCTION_SECURITY_GATES} == {"pending"}
    assert {gate.runtime_enabled for gate in NO_PRODUCTION_SECURITY_GATES} == {False}


def test_no_production_security_gates_point_to_importable_contracts() -> None:
    for module_name in no_production_security_contract_modules():
        assert importlib.import_module(module_name)


def test_no_production_security_evidence_matches_source_contracts() -> None:
    evidence_by_gate = {
        gate.gate_id: gate.evidence_required for gate in NO_PRODUCTION_SECURITY_GATES
    }

    assert evidence_by_gate["NOPROD-SEC-001"] == secret_management_requirement_keys()
    assert evidence_by_gate["NOPROD-SEC-002"] == encryption_at_rest_requirement_keys()
    assert evidence_by_gate["NOPROD-SEC-003"] == backup_restore_requirement_keys()


def test_no_production_security_runtime_status_blocks_phi() -> None:
    assert NO_PRODUCTION_SECURITY_RUNTIME_STATUS == {
        "secret_store_configured": False,
        "encryption_at_rest_verified": False,
        "backup_restore_drill_verified": False,
        "real_phi_allowed": False,
        "reason": (
            "SEC-001/002/003 are contractual gates only; no production secret store, "
            "encryption verification or restore drill has been approved."
        ),
    }
