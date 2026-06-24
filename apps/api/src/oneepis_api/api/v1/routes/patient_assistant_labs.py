from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.clinical_record import (
    ClinicalEvent,
    ClinicalEventType,
    RecordStatus,
)
from oneepis_api.models.lab import LabPanel, LabResult
from oneepis_api.schemas.clinical_record import (
    AssistantChartPoint,
    AssistantChartSeries,
    AssistantCorrelationEvidence,
    AssistantSearchResult,
)

from .patient_assistant_lab_values import (
    contains_any_terms,
    exam_marker,
    exam_results,
    lab_marker,
    lab_matched_fields,
    lab_note,
    lab_result_source_path,
    lab_results_matching,
    lab_summary,
    normalize_series_key,
    numeric_value,
    payload_text,
    payload_text_values,
    truncate,
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
            snippet=lab_summary(result),
            matched_fields=lab_matched_fields(query, result),
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
        marker = lab_marker(result)
        value = numeric_value(result.numeric_value)
        if marker is None or value is None:
            continue
        _append_exam_point(
            grouped,
            include_all=include_all,
            selected=selected,
            key=f"exam:{normalize_series_key(marker)}",
            label=marker,
            unit=result.unit,
            point=AssistantChartPoint(
                occurred_at=result.panel.occurred_at,
                value=value,
                source_type="lab_result",
                source_id=result.id,
                source_path=lab_result_source_path(patient_id, result.panel_id, result.id),
                note=truncate(lab_note(result), 160),
            ),
            source_label="lab_results",
        )
    for event in events:
        for result in exam_results(event.payload):
            marker = exam_marker(result)
            value = numeric_value(result.get("value"))
            if marker is None or value is None:
                continue
            _append_exam_point(
                grouped,
                include_all=include_all,
                selected=selected,
                key=f"exam:{normalize_series_key(marker)}",
                label=marker,
                unit=payload_text(result.get("unit")),
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
            summary=lab_summary(result),
            source_path=lab_result_source_path(patient_id, result.panel_id, result.id),
        )
        for result in lab_results_matching(lab_results, terms)
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
            " ".join(payload_text_values(result)) for result in exam_results(event.payload)
        )
        if contains_any_terms(exam_text, terms):
            matches.append(event)
    return matches


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
