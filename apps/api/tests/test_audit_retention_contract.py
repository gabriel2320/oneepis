import re
from pathlib import Path

from oneepis_api.core.audit_retention_contract import (
    AUDIT_EVENT_PURGE_GUARD_PATTERNS,
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
    forbidden_patterns = _compiled_purge_guard_patterns()

    matches: list[str] = []
    for path in src_root.rglob("*.py"):
        if path.name == "audit_retention_contract.py":
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern.search(text):
                matches.append(f"{path.relative_to(src_root)} matches {pattern.pattern}")

    assert matches == []


def test_audit_event_runtime_purge_guard_blocks_model_derived_sql() -> None:
    forbidden_patterns = _compiled_purge_guard_patterns()
    unsafe_snippets = (
        'session.execute(text(f"DELETE FROM {AuditEvent.__tablename__}"))',
        'session.execute(text(f"TRUNCATE TABLE {AuditEvent.__tablename__}"))',
        'session.execute(text(f"DROP TABLE IF EXISTS {AuditEvent.__tablename__}"))',
        'session.execute(text("DELETE FROM " + AuditEvent.__tablename__))',
        'session.execute(text("TRUNCATE TABLE " + AuditEvent.__tablename__))',
        'session.execute(text("DROP TABLE IF EXISTS " + AuditEvent.__tablename__))',
    )

    misses = [
        snippet
        for snippet in unsafe_snippets
        if not any(pattern.search(snippet) for pattern in forbidden_patterns)
    ]

    assert misses == []


def test_audit_event_retention_guard_allows_read_queries() -> None:
    read_query = "session.execute(select(AuditEvent).where(AuditEvent.action == 'record.read'))"

    assert "AuditEvent" in read_query
    assert not re.search(r"\bdelete\s+from\s+audit_events\b", read_query, re.IGNORECASE)
    assert not re.search(r"\btruncate\s+(?:table\s+)?audit_events\b", read_query, re.IGNORECASE)
    assert not any(pattern.search(read_query) for pattern in _compiled_purge_guard_patterns())


def _compiled_purge_guard_patterns() -> tuple[re.Pattern[str], ...]:
    return tuple(
        re.compile(pattern, re.IGNORECASE) for pattern in AUDIT_EVENT_PURGE_GUARD_PATTERNS
    )
