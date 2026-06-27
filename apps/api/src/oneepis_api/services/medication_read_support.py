from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from oneepis_api.models.clinical_record import Medication


def medication_source(medication: Medication) -> dict[str, Any] | None:
    catalog_item = medication.catalog_item
    if catalog_item is not None:
        return {
            "source_system": catalog_item.source_system.value,
            "source_label": catalog_item.source_label,
            "source_url": catalog_item.source_url,
            "external_id": catalog_item.external_id,
            "source_version": catalog_item.source_version,
            "retrieved_at": catalog_item.retrieved_at,
            "reviewed_at": catalog_item.reviewed_at,
            "review_status": catalog_item.review_status.value,
        }
    source_refs = medication.dose_check_snapshot.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        return None
    first_source = source_refs[0]
    if not isinstance(first_source, dict):
        return None
    if not first_source.get("source_system") or not first_source.get("source_label"):
        return None
    return {
        "source_system": first_source["source_system"],
        "source_label": first_source["source_label"],
        "source_url": first_source.get("source_url"),
        "external_id": first_source.get("external_id"),
        "source_version": first_source.get("source_version"),
        "retrieved_at": first_source.get("retrieved_at"),
        "reviewed_at": first_source.get("reviewed_at"),
        "review_status": first_source.get("review_status") or "draft",
    }


def medication_missing_fields(medication: Medication) -> list[str]:
    missing = [
        field
        for field in ("dose", "route", "frequency")
        if not getattr(medication, field)
    ]
    if medication_source(medication) is None:
        missing.append("source")
    return missing
