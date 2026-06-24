from __future__ import annotations

import uuid
from unicodedata import combining, normalize

from oneepis_api.models.lab import LabResult, LabResultFlag


def lab_result_source_path(
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
    result_id: uuid.UUID,
) -> str:
    return f"/api/v1/patients/{patient_id}/lab-panels/{panel_id}/results/{result_id}"


def lab_results_matching(lab_results: list[LabResult], terms: tuple[str, ...]) -> list[LabResult]:
    return [
        result
        for result in lab_results
        if contains_any_terms(
            " ".join(
                value
                for value in (
                    result.code,
                    result.name,
                    result.value,
                    result.unit,
                    result.reference_range,
                    result.notes,
                )
                if value
            ),
            terms,
        )
    ]


def lab_matched_fields(query: str, result: LabResult) -> list[str]:
    values = {
        "code": result.code,
        "name": result.name,
        "value": result.value,
        "unit": result.unit,
        "reference_range": result.reference_range,
        "notes": result.notes,
        "panel_name": result.panel.panel_name,
        "panel_summary": result.panel.summary,
    }
    normalized_query = normalize_for_match(query)
    return [
        field
        for field, value in values.items()
        if value and normalized_query in normalize_for_match(str(value))
    ]


def lab_marker(result: LabResult) -> str | None:
    return payload_text(result.code or result.name)


def lab_note(result: LabResult) -> str:
    values = [result.panel.panel_name, result.notes, result.flag.value]
    return " / ".join(value for value in values if value)


def lab_summary(result: LabResult) -> str:
    value = result.value
    if value is None and result.numeric_value is not None:
        value = str(result.numeric_value)
    value = value or ""
    unit = f" {result.unit}" if result.unit else ""
    flag = f" ({result.flag.value})" if result.flag != LabResultFlag.UNKNOWN else ""
    return f"{result.name}: {value}{unit}{flag}".strip()


def exam_results(payload: dict[str, object]) -> list[dict[str, object]]:
    raw_results = payload.get("results")
    if isinstance(raw_results, list):
        return [result for result in raw_results if isinstance(result, dict)]
    return [payload]


def exam_marker(payload: dict[str, object]) -> str | None:
    return payload_text(payload.get("code") or payload.get("name") or payload.get("marker"))


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


def numeric_value(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def contains_any_terms(value: str, terms: tuple[str, ...]) -> bool:
    normalized_value = normalize_for_match(value)
    return any(normalize_for_match(term) in normalized_value for term in terms)


def normalize_series_key(value: str) -> str:
    return normalize_for_match(value.strip()).replace(" ", "_")


def truncate(value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."


def normalize_for_match(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(character for character in decomposed if not combining(character))
