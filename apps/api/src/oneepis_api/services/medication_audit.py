from __future__ import annotations

from typing import Any

MEDICATION_CREATE_AUDIT_FIELDS = [
    "catalog_item_id",
    "patient_id",
    "started_on",
    "ended_on",
    "status",
]
MEDICATION_UPDATE_AUDIT_FIELDS = set(MEDICATION_CREATE_AUDIT_FIELDS)


def medication_dose_audit_metadata(
    dose_check_snapshot: dict[str, Any],
    override_reason: str | None,
) -> dict[str, Any]:
    warnings = dose_check_snapshot.get("warnings")
    source_refs = dose_check_snapshot.get("source_refs")
    warning_items = warnings if isinstance(warnings, list) else []
    source_items = source_refs if isinstance(source_refs, list) else []
    reason = override_reason.strip() if override_reason else ""
    severities = sorted(
        {
            str(item.get("severity"))
            for item in warning_items
            if isinstance(item, dict) and item.get("severity")
        }
    )
    return {
        "dose_validation_blocking": bool(dose_check_snapshot.get("blocking")),
        "dose_warning_count": len(warning_items),
        "dose_warning_severities": severities,
        "dose_override": bool(reason),
        "dose_override_reason_present": bool(reason),
        "dose_override_reason_length": len(reason),
        "dose_source_count": len(source_items),
    }


def sanitize_override_reason_audit(snapshot: dict[str, Any]) -> None:
    if "dose_override_reason" not in snapshot:
        return
    reason = snapshot["dose_override_reason"]
    if not isinstance(reason, str) or not reason.strip():
        snapshot["dose_override_reason"] = None
        return
    snapshot["dose_override_reason"] = {
        "present": True,
        "length": len(reason.strip()),
    }


def medication_update_audit_fields(fields: list[str]) -> list[str]:
    return [field for field in fields if field in MEDICATION_UPDATE_AUDIT_FIELDS]
