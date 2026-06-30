from pathlib import Path

from oneepis_api.core.audit_retention_contract import (
    AUDIT_EVENT_RETENTION_GUARD,
    AUDIT_RETENTION_REQUIREMENTS,
    audit_retention_requirement_keys,
)
from oneepis_api.models.audit import AuditEvent


def test_audit_retention_contract_tracks_minimum_requirements() -> None:
    assert audit_retention_requirement_keys() == (
        "versioned_retention_policy",
        "exportable_audit_log",
        "immutability_control",
        "legal_hold",
        "reviewed_purge_procedure",
    )

    assert all(requirement.label for requirement in AUDIT_RETENTION_REQUIREMENTS)
    assert all(requirement.criterion for requirement in AUDIT_RETENTION_REQUIREMENTS)
    assert {requirement.status for requirement in AUDIT_RETENTION_REQUIREMENTS} == {
        "required_before_production",
        "required_before_purge",
    }


def test_audit_event_retention_guard_is_bound_to_model_table() -> None:
    assert AUDIT_EVENT_RETENTION_GUARD == {
        "model": "AuditEvent",
        "table": "audit_events",
        "runtime_purge_allowed": False,
        "reason": "No production retention, legal hold or immutable audit store exists yet.",
    }
    assert AuditEvent.__tablename__ == AUDIT_EVENT_RETENTION_GUARD["table"]
    assert AuditEvent.created_at.property.columns[0].nullable is False


def test_audit_event_runtime_purge_is_not_implemented_without_contract() -> None:
    src_root = Path(__file__).parents[1] / "src" / "oneepis_api"
    forbidden_fragments = (
        "delete(AuditEvent",
        "session.delete(AuditEvent",
        "truncate audit_events",
        "drop table audit_events",
    )

    matches: list[str] = []
    for path in src_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_fragments:
            if fragment.lower() in text:
                matches.append(f"{path.relative_to(src_root)} contains {fragment}")

    assert matches == []
