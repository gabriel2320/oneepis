from __future__ import annotations

import logging
from typing import Any

REDACTED = "[REDACTED]"

PHI_SENSITIVE_KEYS = frozenset(
    {
        "access_token",
        "assessment",
        "authorization",
        "birth_date",
        "chief_complaint",
        "clinical_identifier",
        "clinical_note",
        "contact_phone",
        "content",
        "document_id",
        "document_id_hash",
        "email",
        "emergency_contact",
        "first_name",
        "free_text",
        "last_name",
        "national_id",
        "note",
        "notes",
        "objective",
        "password",
        "plan",
        "preferred_name",
        "reason",
        "reaction",
        "refresh_token",
        "subjective",
        "summary",
        "token",
    }
)


def sanitize_for_log(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if _is_sensitive_key(key) else sanitize_for_log(nested)
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [sanitize_for_log(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_for_log(item) for item in value)
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower()
    if normalized in PHI_SENSITIVE_KEYS:
        return True
    return normalized.endswith("_token") or normalized.endswith("_password")


class PhiSafeLoggingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, dict):
            record.msg = sanitize_for_log(record.msg)
        elif record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_for_log(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(sanitize_for_log(arg) for arg in record.args)
        return True


def configure_phi_safe_logging() -> None:
    root = logging.getLogger()
    if any(isinstance(item, PhiSafeLoggingFilter) for item in root.filters):
        return
    root.addFilter(PhiSafeLoggingFilter())
