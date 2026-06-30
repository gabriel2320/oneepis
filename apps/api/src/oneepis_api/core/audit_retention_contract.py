from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AuditRetentionRequirement:
    key: str
    label: str
    criterion: str
    status: Literal["required_before_production", "required_before_purge"]


AUDIT_RETENTION_REQUIREMENTS: tuple[AuditRetentionRequirement, ...] = (
    AuditRetentionRequirement(
        key="versioned_retention_policy",
        label="Versioned retention policy",
        criterion="Retention periods must be approved, versioned and linked to clinical/legal use.",
        status="required_before_production",
    ),
    AuditRetentionRequirement(
        key="exportable_audit_log",
        label="Exportable audit log",
        criterion="Audit events must have a controlled export path for review and legal custody.",
        status="required_before_production",
    ),
    AuditRetentionRequirement(
        key="immutability_control",
        label="Immutability control",
        criterion=(
            "Production audit storage must provide hash-chain, WORM or "
            "equivalent tamper evidence."
        ),
        status="required_before_production",
    ),
    AuditRetentionRequirement(
        key="legal_hold",
        label="Legal hold",
        criterion="Retention must support explicit hold before any purge, deletion or compaction.",
        status="required_before_purge",
    ),
    AuditRetentionRequirement(
        key="reviewed_purge_procedure",
        label="Reviewed purge procedure",
        criterion="Any purge must be documented, reviewed, authorized and itself audited.",
        status="required_before_purge",
    ),
)


AUDIT_EVENT_RETENTION_GUARD = {
    "model": "AuditEvent",
    "table": "audit_events",
    "runtime_purge_allowed": False,
    "reason": "No production retention, legal hold or immutable audit store exists yet.",
}

AUDIT_EVENT_PURGE_GUARD_PATTERNS: tuple[str, ...] = (
    r"\bdelete\s*\(\s*AuditEvent\b",
    r"\bsession\.delete\s*\(\s*AuditEvent\b",
    r"\bdelete\s+from\s+audit_events\b",
    r"\btruncate\s+(?:table\s+)?audit_events\b",
    r"\bdrop\s+table\s+(?:if\s+exists\s+)?audit_events\b",
    (
        r"\bsession\.execute\s*\(\s*(?:text\s*\()?['\"][^'\"]*"
        r"(?:delete\s+from|truncate(?:\s+table)?|drop\s+table)"
        r"\s+audit_events\b"
    ),
    (
        r"f['\"][^'\"]*"
        r"(?:delete\s+from|truncate(?:\s+table)?|drop\s+table(?:\s+if\s+exists)?)"
        r"\s*\{\s*AuditEvent\.__tablename__\s*\}"
    ),
    (
        r"['\"][^'\"]*"
        r"(?:delete\s+from|truncate(?:\s+table)?|drop\s+table(?:\s+if\s+exists)?)"
        r"\s*['\"]\s*\+\s*AuditEvent\.__tablename__\b"
    ),
)


def audit_retention_requirement_keys() -> tuple[str, ...]:
    return tuple(requirement.key for requirement in AUDIT_RETENTION_REQUIREMENTS)
