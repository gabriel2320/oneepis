from __future__ import annotations

import uuid
from datetime import date, datetime, time
from unicodedata import combining, normalize

from sqlalchemy import or_

from oneepis_api.models.clinical_record import (
    ClinicalEntry,
    ClinicalEvent,
    Medication,
)
from oneepis_api.models.vital_sign import VitalSign

VITAL_CHART_SERIES = {
    "temperature_c": ("Temperatura", "C", "temperature_c"),
    "systolic_bp": ("Presion sistolica", "mmHg", "systolic_bp"),
    "diastolic_bp": ("Presion diastolica", "mmHg", "diastolic_bp"),
    "heart_rate_bpm": ("Frecuencia cardiaca", "lpm", "heart_rate_bpm"),
    "respiratory_rate_bpm": ("Frecuencia respiratoria", "rpm", "respiratory_rate_bpm"),
    "oxygen_saturation_pct": ("Saturacion O2", "%", "oxygen_saturation_pct"),
}
ASSISTANT_CORRELATION_PRESETS = (
    "fever_infection",
    "renal_medications",
    "respiratory_oxygen",
    "hemoglobin_bleeding",
    "medication_changes",
)


def clinical_event_source_path(patient_id: uuid.UUID, event_id: uuid.UUID) -> str:
    return f"/api/v1/patients/{patient_id}/clinical-events/{event_id}"


def entry_sections(entry: ClinicalEntry) -> list[str]:
    return [
        text
        for text in (entry.subjective, entry.objective, entry.assessment, entry.plan)
        if text
    ]


def vital_summary(vital: VitalSign) -> str:
    values = []
    if vital.temperature_c is not None:
        values.append(f"T {vital.temperature_c} C")
    if vital.systolic_bp is not None and vital.diastolic_bp is not None:
        values.append(f"PA {vital.systolic_bp}/{vital.diastolic_bp}")
    if vital.heart_rate_bpm is not None:
        values.append(f"FC {vital.heart_rate_bpm}")
    if vital.respiratory_rate_bpm is not None:
        values.append(f"FR {vital.respiratory_rate_bpm}")
    if vital.oxygen_saturation_pct is not None:
        values.append(f"SatO2 {vital.oxygen_saturation_pct}%")
    return truncate(", ".join(values) or vital.notes or "Signos vitales registrados")


def medication_summary(medication: Medication) -> str:
    values = [
        value
        for value in (
            medication.dose,
            medication.route,
            medication.frequency,
            medication.status.value,
        )
        if value
    ]
    return truncate(", ".join(values) or medication.status.value)


def date_or_created_at(value: date | None, fallback: datetime) -> datetime:
    if value is None:
        return fallback
    return datetime.combine(value, time.min, tzinfo=fallback.tzinfo)


def events_matching(events: list[ClinicalEvent], *terms: str) -> list[ClinicalEvent]:
    return [
        event
        for event in events
        if contains_any_terms(
            " ".join(
                [
                    event.summary,
                    event.event_type.value,
                    *payload_text_values(event.payload),
                ]
            ),
            terms,
        )
    ]


def medications_matching(medications: list[Medication], *terms: str) -> list[Medication]:
    return [
        medication
        for medication in medications
        if contains_any_terms(
            " ".join(
                value
                for value in (
                    medication.name,
                    medication.dose,
                    medication.route,
                    medication.frequency,
                )
                if value
            ),
            terms,
        )
    ]


def contains_any_terms(value: str, terms: tuple[str, ...]) -> bool:
    normalized_value = normalize_for_match(value)
    return any(normalize_for_match(term) in normalized_value for term in terms)


def match_columns(pattern: str, *columns: object):
    return or_(*(column.ilike(pattern, escape="\\") for column in columns))


def like_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def matched_fields(query: str, fields: dict[str, str | None]) -> list[str]:
    normalized_query = normalize_for_match(query)
    matches = [
        name
        for name, value in fields.items()
        if value and normalized_query in normalize_for_match(value)
    ]
    return matches or ["summary"]


def snippet(query: str, *values: str | None) -> str:
    normalized_query = normalize_for_match(query)
    texts = [collapse(value) for value in values if value]
    for text in texts:
        if normalized_query in normalize_for_match(text):
            return truncate(text)
    return truncate(" / ".join(texts) or "Resultado clinico estructurado")


def collapse(value: str) -> str:
    return " ".join(value.split())


def normalize_for_match(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(character for character in decomposed if not combining(character))


def normalize_series_key(value: str) -> str:
    return normalize_for_match(value.strip()).replace(" ", "_")


def numeric_value(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def payload_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def payload_text_values(value: object) -> list[str]:
    if isinstance(value, dict):
        values = []
        for child_value in value.values():
            values.extend(payload_text_values(child_value))
        return values
    if isinstance(value, list):
        values = []
        for child_value in value:
            values.extend(payload_text_values(child_value))
        return values
    text = payload_text(value)
    return [text] if text else []


def truncate(value: str, max_length: int = 320) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."
