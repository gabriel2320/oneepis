from __future__ import annotations

import uuid
from unicodedata import combining, normalize

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.clinical_record import (
    ClinicalEvent,
    ClinicalEventType,
    RecordStatus,
)
from oneepis_api.models.lab import LabPanel, LabResult, LabResultFlag
from oneepis_api.schemas.clinical_record import (
    AssistantChartPoint,
    AssistantChartSeries,
    AssistantCorrelationEvidence,
    AssistantSearchResult,
)


def fetch_lab_results_for_assistant(
    session: Session,
    patient_id: uuid.UUID,
    limit: int,
) -> list[LabResult]:
    statement = (
        select(LabResult)
        .join(LabPanel)
        .options(selectinload(LabResult.panel))
        .where(
            LabResult.patient_id == patient_id,
            LabResult.status == RecordStatus.ACTIVE,
            LabResult.numeric_value.is_not(None),
            LabPanel.status == RecordStatus.ACTIVE,
        )
        .order_by(LabPanel.occurred_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def search_lab_results_for_assistant(
    session: Session,
    patient_id: uuid.UUID,
    pattern: str,
    limit: int,
) -> list[LabResult]:
    statement = (
        select(LabResult)
        .join(LabPanel)
        .options(selectinload(LabResult.panel))
        .where(
            LabResult.patient_id == patient_id,
            LabResult.status == RecordStatus.ACTIVE,
            LabPanel.status == RecordStatus.ACTIVE,
            or_(
                LabResult.code.ilike(pattern),
                LabResult.name.ilike(pattern),
                LabResult.value.ilike(pattern),
                LabResult.unit.ilike(pattern),
                LabResult.reference_range.ilike(pattern),
                LabResult.notes.ilike(pattern),
                LabPanel.panel_name.ilike(pattern),
                LabPanel.summary.ilike(pattern),
            ),
        )
        .order_by(LabPanel.occurred_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def lab_search_results(
    query: str,
    patient_id: uuid.UUID,
    lab_results: list[LabResult],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="lab_result",
            item_id=result.id,
            occurred_at=result.panel.occurred_at,
            label=result.name,
            snippet=_lab_summary(result),
            matched_fields=_lab_matched_fields(query, result),
            source_label="lab_results",
            source_path=lab_result_source_path(patient_id, result.panel_id, result.id),
        )
        for result in lab_results
    ]


def exam_chart_series(
    patient_id: uuid.UUID,
    lab_results: list[LabResult],
    events: list[ClinicalEvent],
    selected: set[str],
) -> list[AssistantChartSeries]:
    include_all = not selected or "exam_result" in selected
    grouped: dict[str, AssistantChartSeries] = {}
    for result in lab_results:
        marker = _lab_marker(result)
        value = _numeric_value(result.numeric_value)
        if marker is None or value is None:
            continue
        _append_exam_point(
            grouped,
            include_all=include_all,
            selected=selected,
            key=f"exam:{_normalize_series_key(marker)}",
            label=marker,
            unit=result.unit,
            point=AssistantChartPoint(
                occurred_at=result.panel.occurred_at,
                value=value,
                source_type="lab_result",
                source_id=result.id,
                source_path=lab_result_source_path(patient_id, result.panel_id, result.id),
                note=_truncate(_lab_note(result), 160),
            ),
            source_label="lab_results",
        )
    for event in events:
        for result in _exam_results(event.payload):
            marker = _exam_marker(result)
            value = _numeric_value(result.get("value"))
            if marker is None or value is None:
                continue
            _append_exam_point(
                grouped,
                include_all=include_all,
                selected=selected,
                key=f"exam:{_normalize_series_key(marker)}",
                label=marker,
                unit=_payload_text(result.get("unit")),
                point=AssistantChartPoint(
                    occurred_at=event.occurred_at,
                    value=value,
                    source_type="clinical_event",
                    source_id=event.id,
                    source_path=f"/api/v1/patients/{patient_id}/clinical-events/{event.id}",
                    note=event.summary,
                ),
                source_label="clinical_events.exam_result",
            )
    for series in grouped.values():
        series.points.sort(key=lambda point: point.occurred_at)
    return list(grouped.values())


def lab_result_evidence(
    patient_id: uuid.UUID,
    lab_results: list[LabResult],
    terms: tuple[str, ...],
    *,
    label: str,
) -> list[AssistantCorrelationEvidence]:
    return [
        AssistantCorrelationEvidence(
            source_type="lab_result",
            source_id=result.id,
            occurred_at=result.panel.occurred_at,
            label=label,
            summary=_lab_summary(result),
            source_path=lab_result_source_path(patient_id, result.panel_id, result.id),
        )
        for result in _lab_results_matching(lab_results, terms)
    ]


def exam_events_matching(
    events: list[ClinicalEvent],
    terms: tuple[str, ...],
) -> list[ClinicalEvent]:
    matches = []
    for event in events:
        if event.event_type != ClinicalEventType.EXAM_RESULT:
            continue
        exam_text = " ".join(
            " ".join(_payload_text_values(result)) for result in _exam_results(event.payload)
        )
        if _contains_any_terms(exam_text, terms):
            matches.append(event)
    return matches


def lab_result_source_path(
    patient_id: uuid.UUID,
    panel_id: uuid.UUID,
    result_id: uuid.UUID,
) -> str:
    return f"/api/v1/patients/{patient_id}/lab-panels/{panel_id}/results/{result_id}"


def _append_exam_point(
    grouped: dict[str, AssistantChartSeries],
    *,
    include_all: bool,
    selected: set[str],
    key: str,
    label: str,
    unit: str | None,
    point: AssistantChartPoint,
    source_label: str,
) -> None:
    if not include_all and key not in selected:
        return
    series = grouped.setdefault(
        key,
        AssistantChartSeries(key=key, label=label, unit=unit, source_label=source_label),
    )
    if source_label not in series.source_label.split(" + "):
        series.source_label = f"{series.source_label} + {source_label}"
    series.points.append(point)


def _lab_results_matching(lab_results: list[LabResult], terms: tuple[str, ...]) -> list[LabResult]:
    return [
        result
        for result in lab_results
        if _contains_any_terms(
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


def _lab_matched_fields(query: str, result: LabResult) -> list[str]:
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
    normalized_query = _normalize_for_match(query)
    return [
        field
        for field, value in values.items()
        if value and normalized_query in _normalize_for_match(str(value))
    ]


def _lab_marker(result: LabResult) -> str | None:
    return _payload_text(result.code or result.name)


def _lab_note(result: LabResult) -> str:
    values = [result.panel.panel_name, result.notes, result.flag.value]
    return " / ".join(value for value in values if value)


def _lab_summary(result: LabResult) -> str:
    value = result.value
    if value is None and result.numeric_value is not None:
        value = str(result.numeric_value)
    value = value or ""
    unit = f" {result.unit}" if result.unit else ""
    flag = f" ({result.flag.value})" if result.flag != LabResultFlag.UNKNOWN else ""
    return f"{result.name}: {value}{unit}{flag}".strip()


def _exam_results(payload: dict[str, object]) -> list[dict[str, object]]:
    raw_results = payload.get("results")
    if isinstance(raw_results, list):
        return [result for result in raw_results if isinstance(result, dict)]
    return [payload]


def _exam_marker(payload: dict[str, object]) -> str | None:
    return _payload_text(payload.get("code") or payload.get("name") or payload.get("marker"))


def _payload_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _payload_text_values(value: object) -> list[str]:
    if isinstance(value, dict):
        values = []
        for child_value in value.values():
            values.extend(_payload_text_values(child_value))
        return values
    if isinstance(value, list):
        values = []
        for child_value in value:
            values.extend(_payload_text_values(child_value))
        return values
    text = _payload_text(value)
    return [text] if text else []


def _numeric_value(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _contains_any_terms(value: str, terms: tuple[str, ...]) -> bool:
    normalized_value = _normalize_for_match(value)
    return any(_normalize_for_match(term) in normalized_value for term in terms)


def _normalize_series_key(value: str) -> str:
    return _normalize_for_match(value.strip()).replace(" ", "_")


def _normalize_for_match(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(character for character in decomposed if not combining(character))


def _truncate(value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."
