from __future__ import annotations

import logging
import re
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

_SENSITIVE_KEY_PATTERN = "|".join(
    re.escape(key) for key in sorted(PHI_SENSITIVE_KEYS, key=len, reverse=True)
)
_DYNAMIC_SECRET_KEY_PATTERN = r"[a-zA-Z0-9_]*(?:_token|_password)"
_FLAT_QUOTED_FIELD_RE = re.compile(
    rf"(?P<prefix>['\"]?(?:{_SENSITIVE_KEY_PATTERN}|{_DYNAMIC_SECRET_KEY_PATTERN})['\"]?\s*[:=]\s*)"
    r"(?P<quote>['\"])(?P<value>.*?)(?P=quote)",
    re.IGNORECASE,
)
_FLAT_BARE_FIELD_RE = re.compile(
    rf"(?P<prefix>['\"]?(?:{_SENSITIVE_KEY_PATTERN}|{_DYNAMIC_SECRET_KEY_PATTERN})['\"]?\s*[:=]\s*)"
    r"(?P<value>[^,;\s}'\"]+)",
    re.IGNORECASE,
)


def sanitize_for_log(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if _is_sensitive_key(key) else sanitize_for_log(nested)
            for key, nested in value.items()
        }
    if isinstance(value, str):
        return _sanitize_flat_text(value)
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


def _sanitize_flat_text(value: str) -> str:
    value = _FLAT_QUOTED_FIELD_RE.sub(_redact_quoted_field, value)
    return _FLAT_BARE_FIELD_RE.sub(
        lambda match: f"{match.group('prefix')}{REDACTED}",
        value,
    )


def _redact_quoted_field(match: re.Match[str]) -> str:
    quote = match.group("quote")
    return f"{match.group('prefix')}{quote}{REDACTED}{quote}"


class PhiSafeLoggingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, (dict, str)):
            record.msg = sanitize_for_log(record.msg)
        if record.args:
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
