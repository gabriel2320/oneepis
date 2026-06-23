from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Annotated
from unicodedata import combining, normalize

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select

from oneepis_api.models.clinical_record import (
    ActiveProblem,
    Allergy,
    ClinicalEncounter,
    ClinicalEntry,
    ClinicalEvent,
    ClinicalEventType,
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.schemas.clinical_record import (
    AssistantChartPoint,
    AssistantChartRequest,
    AssistantChartResponse,
    AssistantChartSeries,
    AssistantSearchResponse,
    AssistantSearchResult,
    AssistantTimelineItem,
    AssistantTimelineResponse,
)

from .patient_shared import PATIENT_ROUTER_OPTIONS, LimitQuery, SessionDep, require_patient

router = APIRouter(**PATIENT_ROUTER_OPTIONS)
AssistantSearchQuery = Annotated[str, Query(alias="q", min_length=2, max_length=120)]
VITAL_CHART_SERIES = {
    "temperature_c": ("Temperatura", "C", "temperature_c"),
    "systolic_bp": ("Presion sistolica", "mmHg", "systolic_bp"),
    "diastolic_bp": ("Presion diastolica", "mmHg", "diastolic_bp"),
    "heart_rate_bpm": ("Frecuencia cardiaca", "lpm", "heart_rate_bpm"),
    "respiratory_rate_bpm": ("Frecuencia respiratoria", "rpm", "respiratory_rate_bpm"),
    "oxygen_saturation_pct": ("Saturacion O2", "%", "oxygen_saturation_pct"),
}


@router.get("/{patient_id}/assistant/timeline", response_model=AssistantTimelineResponse)
def get_assistant_timeline(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
) -> AssistantTimelineResponse:
    require_patient(session, patient_id)
    query_limit = limit + 1
    encounters = list(
        session.scalars(
            select(ClinicalEncounter)
            .where(ClinicalEncounter.patient_id == patient_id)
            .order_by(ClinicalEncounter.started_at.desc())
            .limit(query_limit)
        )
    )
    entries = list(
        session.scalars(
            select(ClinicalEntry)
            .where(ClinicalEntry.patient_id == patient_id)
            .order_by(ClinicalEntry.occurred_at.desc())
            .limit(query_limit)
        )
    )
    events = list(
        session.scalars(
            select(ClinicalEvent)
            .where(ClinicalEvent.patient_id == patient_id)
            .order_by(ClinicalEvent.occurred_at.desc())
            .limit(query_limit)
        )
    )
    vitals = list(
        session.scalars(
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
            .order_by(VitalSign.measured_at.desc())
            .limit(query_limit)
        )
    )
    medications = list(
        session.scalars(
            select(Medication)
            .where(Medication.patient_id == patient_id, Medication.status == RecordStatus.ACTIVE)
            .order_by(Medication.created_at.desc())
            .limit(query_limit)
        )
    )
    problems = list(
        session.scalars(
            select(ActiveProblem)
            .where(
                ActiveProblem.patient_id == patient_id,
                ActiveProblem.status == RecordStatus.ACTIVE,
            )
            .order_by(ActiveProblem.created_at.desc())
            .limit(query_limit)
        )
    )
    allergies = list(
        session.scalars(
            select(Allergy)
            .where(Allergy.patient_id == patient_id, Allergy.status == RecordStatus.ACTIVE)
            .order_by(Allergy.recorded_at.desc())
            .limit(query_limit)
        )
    )
    items = [
        *_encounter_items(patient_id, encounters),
        *_entry_items(patient_id, entries),
        *_event_items(patient_id, events),
        *_vital_items(patient_id, vitals),
        *_medication_items(patient_id, medications),
        *_problem_items(patient_id, problems),
        *_allergy_items(patient_id, allergies),
    ]
    items.sort(key=lambda item: item.occurred_at, reverse=True)
    has_more = len(items) > limit or any(
        len(domain_items) > limit
        for domain_items in (encounters, entries, events, vitals, medications, problems, allergies)
    )
    return AssistantTimelineResponse(
        patient_id=patient_id,
        items=items[:limit],
        missing_data=_missing_data(
            encounters=encounters,
            entries=entries,
            events=events,
            vitals=vitals,
            medications=medications,
            problems=problems,
            allergies=allergies,
        ),
        warnings=_warnings(has_more=has_more, limit=limit),
        limit=limit,
        has_more=has_more,
    )


@router.get("/{patient_id}/assistant/search", response_model=AssistantSearchResponse)
def search_assistant_read_layer(
    patient_id: uuid.UUID,
    session: SessionDep,
    q: AssistantSearchQuery,
    limit: LimitQuery = 20,
) -> AssistantSearchResponse:
    require_patient(session, patient_id)
    query = q.strip()
    if len(query) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query must contain at least 2 non-space characters.",
        )
    query_limit = limit + 1
    pattern = _like_pattern(query)
    encounters = list(
        session.scalars(
            select(ClinicalEncounter)
            .where(
                ClinicalEncounter.patient_id == patient_id,
                _match_columns(
                    pattern,
                    ClinicalEncounter.reason,
                    ClinicalEncounter.location_label,
                    ClinicalEncounter.notes,
                ),
            )
            .order_by(ClinicalEncounter.started_at.desc())
            .limit(query_limit)
        )
    )
    entries = list(
        session.scalars(
            select(ClinicalEntry)
            .where(
                ClinicalEntry.patient_id == patient_id,
                _match_columns(
                    pattern,
                    ClinicalEntry.title,
                    ClinicalEntry.subjective,
                    ClinicalEntry.objective,
                    ClinicalEntry.assessment,
                    ClinicalEntry.plan,
                ),
            )
            .order_by(ClinicalEntry.occurred_at.desc())
            .limit(query_limit)
        )
    )
    events = list(
        session.scalars(
            select(ClinicalEvent)
            .where(
                ClinicalEvent.patient_id == patient_id,
                _match_columns(pattern, ClinicalEvent.summary),
            )
            .order_by(ClinicalEvent.occurred_at.desc())
            .limit(query_limit)
        )
    )
    vitals = list(
        session.scalars(
            select(VitalSign)
            .where(
                VitalSign.patient_id == patient_id,
                _match_columns(pattern, VitalSign.notes),
            )
            .order_by(VitalSign.measured_at.desc())
            .limit(query_limit)
        )
    )
    medications = list(
        session.scalars(
            select(Medication)
            .where(
                Medication.patient_id == patient_id,
                Medication.status == RecordStatus.ACTIVE,
                _match_columns(
                    pattern,
                    Medication.name,
                    Medication.dose,
                    Medication.route,
                    Medication.frequency,
                ),
            )
            .order_by(Medication.created_at.desc())
            .limit(query_limit)
        )
    )
    problems = list(
        session.scalars(
            select(ActiveProblem)
            .where(
                ActiveProblem.patient_id == patient_id,
                ActiveProblem.status == RecordStatus.ACTIVE,
                _match_columns(
                    pattern,
                    ActiveProblem.title,
                    ActiveProblem.code,
                    ActiveProblem.notes,
                ),
            )
            .order_by(ActiveProblem.created_at.desc())
            .limit(query_limit)
        )
    )
    allergies = list(
        session.scalars(
            select(Allergy)
            .where(
                Allergy.patient_id == patient_id,
                Allergy.status == RecordStatus.ACTIVE,
                _match_columns(pattern, Allergy.substance, Allergy.reaction),
            )
            .order_by(Allergy.recorded_at.desc())
            .limit(query_limit)
        )
    )
    results = [
        *_encounter_search_results(query, patient_id, encounters),
        *_entry_search_results(query, patient_id, entries),
        *_event_search_results(query, patient_id, events),
        *_vital_search_results(query, patient_id, vitals),
        *_medication_search_results(query, patient_id, medications),
        *_problem_search_results(query, patient_id, problems),
        *_allergy_search_results(query, patient_id, allergies),
    ]
    results.sort(key=lambda item: item.occurred_at, reverse=True)
    has_more = len(results) > limit or any(
        len(domain_items) > limit
        for domain_items in (encounters, entries, events, vitals, medications, problems, allergies)
    )
    return AssistantSearchResponse(
        patient_id=patient_id,
        query=query,
        results=results[:limit],
        missing_data=_search_missing_data(results),
        warnings=_search_warnings(has_more=has_more, limit=limit),
        limit=limit,
        has_more=has_more,
    )


@router.post("/{patient_id}/assistant/chart", response_model=AssistantChartResponse)
def get_assistant_chart_data(
    patient_id: uuid.UUID,
    payload: AssistantChartRequest,
    session: SessionDep,
) -> AssistantChartResponse:
    require_patient(session, patient_id)
    selected = {_normalize_series_key(series) for series in payload.series if series.strip()}
    query_limit = payload.limit + 1
    vitals = list(
        session.scalars(
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
            .order_by(VitalSign.measured_at.desc())
            .limit(query_limit)
        )
    )
    exam_events = list(
        session.scalars(
            select(ClinicalEvent)
            .where(
                ClinicalEvent.patient_id == patient_id,
                ClinicalEvent.event_type == ClinicalEventType.EXAM_RESULT,
            )
            .order_by(ClinicalEvent.occurred_at.desc())
            .limit(query_limit)
        )
    )
    series = [
        *_vital_chart_series(patient_id, list(reversed(vitals)), selected),
        *_exam_chart_series(patient_id, list(reversed(exam_events)), selected),
    ]
    has_more = len(vitals) > payload.limit or len(exam_events) > payload.limit
    return AssistantChartResponse(
        patient_id=patient_id,
        series=series,
        missing_data=_chart_missing_data(
            series=series,
            vitals=vitals,
            exam_events=exam_events,
        ),
        warnings=_chart_warnings(
            selected=selected,
            has_more=has_more,
            limit=payload.limit,
        ),
        limit=payload.limit,
        has_more=has_more,
    )


def _encounter_items(
    patient_id: uuid.UUID,
    encounters: list[ClinicalEncounter],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="encounter",
            item_id=encounter.id,
            occurred_at=encounter.started_at,
            label="Encuentro clinico",
            summary=f"{encounter.reason} ({encounter.type.value}, {encounter.status.value})",
            source_label="encounters",
            source_path=f"/api/v1/patients/{patient_id}/encounters/{encounter.id}",
        )
        for encounter in encounters
    ]


def _entry_items(
    patient_id: uuid.UUID,
    entries: list[ClinicalEntry],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="clinical_entry",
            item_id=entry.id,
            occurred_at=entry.occurred_at,
            label=entry.title,
            summary=_truncate(" / ".join(_entry_sections(entry)) or entry.kind.value),
            source_label="clinical_entries",
            source_path=f"/api/v1/patients/{patient_id}/clinical-entries/{entry.id}",
        )
        for entry in entries
    ]


def _event_items(
    patient_id: uuid.UUID,
    events: list[ClinicalEvent],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="clinical_event",
            item_id=event.id,
            occurred_at=event.occurred_at,
            label=event.event_type.value,
            summary=event.summary,
            source_label="clinical_events",
            source_path=f"/api/v1/patients/{patient_id}/clinical-events",
        )
        for event in events
    ]


def _vital_items(
    patient_id: uuid.UUID,
    vitals: list[VitalSign],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="vital_sign",
            item_id=vital.id,
            occurred_at=vital.measured_at,
            label="Signos vitales",
            summary=_vital_summary(vital),
            source_label="vital_signs",
            source_path=f"/api/v1/patients/{patient_id}/vital-signs/{vital.id}",
        )
        for vital in vitals
    ]


def _medication_items(
    patient_id: uuid.UUID,
    medications: list[Medication],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="medication",
            item_id=medication.id,
            occurred_at=_date_or_created_at(medication.started_on, medication.created_at),
            label=medication.name,
            summary=_medication_summary(medication),
            source_label="medications",
            source_path=f"/api/v1/patients/{patient_id}/medications/{medication.id}",
        )
        for medication in medications
    ]


def _problem_items(
    patient_id: uuid.UUID,
    problems: list[ActiveProblem],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="problem",
            item_id=problem.id,
            occurred_at=_date_or_created_at(problem.onset_date, problem.created_at),
            label=problem.title,
            summary=_truncate(problem.notes or problem.code or problem.status.value),
            source_label="problems",
            source_path=f"/api/v1/patients/{patient_id}/problems/{problem.id}",
        )
        for problem in problems
    ]


def _allergy_items(
    patient_id: uuid.UUID,
    allergies: list[Allergy],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="allergy",
            item_id=allergy.id,
            occurred_at=allergy.recorded_at,
            label=allergy.substance,
            summary=_truncate(allergy.reaction or allergy.severity.value),
            source_label="allergies",
            source_path=f"/api/v1/patients/{patient_id}/allergies/{allergy.id}",
        )
        for allergy in allergies
    ]


def _encounter_search_results(
    query: str,
    patient_id: uuid.UUID,
    encounters: list[ClinicalEncounter],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="encounter",
            item_id=encounter.id,
            occurred_at=encounter.started_at,
            label="Encuentro clinico",
            snippet=_snippet(query, encounter.reason, encounter.location_label, encounter.notes),
            matched_fields=_matched_fields(
                query,
                {
                    "reason": encounter.reason,
                    "location_label": encounter.location_label,
                    "notes": encounter.notes,
                },
            ),
            source_label="encounters",
            source_path=f"/api/v1/patients/{patient_id}/encounters/{encounter.id}",
        )
        for encounter in encounters
    ]


def _entry_search_results(
    query: str,
    patient_id: uuid.UUID,
    entries: list[ClinicalEntry],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="clinical_entry",
            item_id=entry.id,
            occurred_at=entry.occurred_at,
            label=entry.title,
            snippet=_snippet(
                query,
                entry.title,
                entry.subjective,
                entry.objective,
                entry.assessment,
                entry.plan,
            ),
            matched_fields=_matched_fields(
                query,
                {
                    "title": entry.title,
                    "subjective": entry.subjective,
                    "objective": entry.objective,
                    "assessment": entry.assessment,
                    "plan": entry.plan,
                },
            ),
            source_label="clinical_entries",
            source_path=f"/api/v1/patients/{patient_id}/clinical-entries/{entry.id}",
        )
        for entry in entries
    ]


def _event_search_results(
    query: str,
    patient_id: uuid.UUID,
    events: list[ClinicalEvent],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="clinical_event",
            item_id=event.id,
            occurred_at=event.occurred_at,
            label=event.event_type.value,
            snippet=_snippet(query, event.summary),
            matched_fields=_matched_fields(query, {"summary": event.summary}),
            source_label="clinical_events",
            source_path=f"/api/v1/patients/{patient_id}/clinical-events",
        )
        for event in events
    ]


def _vital_search_results(
    query: str,
    patient_id: uuid.UUID,
    vitals: list[VitalSign],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="vital_sign",
            item_id=vital.id,
            occurred_at=vital.measured_at,
            label="Signos vitales",
            snippet=_snippet(query, vital.notes, _vital_summary(vital)),
            matched_fields=_matched_fields(query, {"notes": vital.notes}),
            source_label="vital_signs",
            source_path=f"/api/v1/patients/{patient_id}/vital-signs/{vital.id}",
        )
        for vital in vitals
    ]


def _medication_search_results(
    query: str,
    patient_id: uuid.UUID,
    medications: list[Medication],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="medication",
            item_id=medication.id,
            occurred_at=_date_or_created_at(medication.started_on, medication.created_at),
            label=medication.name,
            snippet=_snippet(
                query,
                medication.name,
                medication.dose,
                medication.route,
                medication.frequency,
            ),
            matched_fields=_matched_fields(
                query,
                {
                    "name": medication.name,
                    "dose": medication.dose,
                    "route": medication.route,
                    "frequency": medication.frequency,
                },
            ),
            source_label="medications",
            source_path=f"/api/v1/patients/{patient_id}/medications/{medication.id}",
        )
        for medication in medications
    ]


def _problem_search_results(
    query: str,
    patient_id: uuid.UUID,
    problems: list[ActiveProblem],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="problem",
            item_id=problem.id,
            occurred_at=_date_or_created_at(problem.onset_date, problem.created_at),
            label=problem.title,
            snippet=_snippet(query, problem.title, problem.code, problem.notes),
            matched_fields=_matched_fields(
                query,
                {
                    "title": problem.title,
                    "code": problem.code,
                    "notes": problem.notes,
                },
            ),
            source_label="problems",
            source_path=f"/api/v1/patients/{patient_id}/problems/{problem.id}",
        )
        for problem in problems
    ]


def _allergy_search_results(
    query: str,
    patient_id: uuid.UUID,
    allergies: list[Allergy],
) -> list[AssistantSearchResult]:
    return [
        AssistantSearchResult(
            item_type="allergy",
            item_id=allergy.id,
            occurred_at=allergy.recorded_at,
            label=allergy.substance,
            snippet=_snippet(query, allergy.substance, allergy.reaction),
            matched_fields=_matched_fields(
                query,
                {
                    "substance": allergy.substance,
                    "reaction": allergy.reaction,
                },
            ),
            source_label="allergies",
            source_path=f"/api/v1/patients/{patient_id}/allergies/{allergy.id}",
        )
        for allergy in allergies
    ]


def _vital_chart_series(
    patient_id: uuid.UUID,
    vitals: list[VitalSign],
    selected: set[str],
) -> list[AssistantChartSeries]:
    include_all = not selected
    series = []
    for key, (label, unit, attribute) in VITAL_CHART_SERIES.items():
        if not include_all and key not in selected:
            continue
        points = [
            AssistantChartPoint(
                occurred_at=vital.measured_at,
                value=value,
                source_type="vital_sign",
                source_id=vital.id,
                source_path=f"/api/v1/patients/{patient_id}/vital-signs/{vital.id}",
                note=vital.notes,
            )
            for vital in vitals
            if (value := _numeric_value(getattr(vital, attribute))) is not None
        ]
        if points:
            series.append(
                AssistantChartSeries(
                    key=key,
                    label=label,
                    unit=unit,
                    source_label="vital_signs",
                    points=points,
                )
            )
    return series


def _exam_chart_series(
    patient_id: uuid.UUID,
    events: list[ClinicalEvent],
    selected: set[str],
) -> list[AssistantChartSeries]:
    include_all = not selected or "exam_result" in selected
    grouped: dict[str, AssistantChartSeries] = {}
    for event in events:
        for result in _exam_results(event.payload):
            marker = _exam_marker(result)
            value = _numeric_value(result.get("value"))
            if marker is None or value is None:
                continue
            key = f"exam:{_normalize_series_key(marker)}"
            if not include_all and key not in selected:
                continue
            series = grouped.setdefault(
                key,
                AssistantChartSeries(
                    key=key,
                    label=marker,
                    unit=_payload_text(result.get("unit")),
                    source_label="clinical_events.exam_result",
                ),
            )
            series.points.append(
                AssistantChartPoint(
                    occurred_at=event.occurred_at,
                    value=value,
                    source_type="clinical_event",
                    source_id=event.id,
                    source_path=f"/api/v1/patients/{patient_id}/clinical-events",
                    note=event.summary,
                )
            )
    return list(grouped.values())


def _entry_sections(entry: ClinicalEntry) -> list[str]:
    return [
        text
        for text in (entry.subjective, entry.objective, entry.assessment, entry.plan)
        if text
    ]


def _vital_summary(vital: VitalSign) -> str:
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
    return _truncate(", ".join(values) or vital.notes or "Signos vitales registrados")


def _medication_summary(medication: Medication) -> str:
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
    return _truncate(", ".join(values) or medication.status.value)


def _date_or_created_at(value: date | None, fallback: datetime) -> datetime:
    if value is None:
        return fallback
    return datetime.combine(value, time.min, tzinfo=fallback.tzinfo)


def _missing_data(
    *,
    encounters: list[ClinicalEncounter],
    entries: list[ClinicalEntry],
    events: list[ClinicalEvent],
    vitals: list[VitalSign],
    medications: list[Medication],
    problems: list[ActiveProblem],
    allergies: list[Allergy],
) -> list[str]:
    missing = []
    if not encounters:
        missing.append("No hay encuentros clinicos estructurados.")
    if not entries:
        missing.append("No hay evoluciones o notas clinicas estructuradas.")
    if not events:
        missing.append("No hay eventos clinicos longitudinales.")
    if not vitals:
        missing.append("No hay signos vitales estructurados.")
    if not medications:
        missing.append("No hay medicacion activa estructurada.")
    if not problems:
        missing.append("No hay problemas activos estructurados.")
    if not allergies:
        missing.append("No hay alergias activas estructuradas.")
    return missing


def _warnings(*, has_more: bool, limit: int) -> list[str]:
    if not has_more:
        return []
    return [f"Timeline limitado a {limit} items; aumenta limit o consulta dominios fuente."]


def _search_missing_data(results: list[AssistantSearchResult]) -> list[str]:
    if results:
        return []
    return ["No se encontraron coincidencias clinicas estructuradas para la busqueda."]


def _search_warnings(*, has_more: bool, limit: int) -> list[str]:
    if not has_more:
        return []
    return [f"Busqueda limitada a {limit} resultados; afina la consulta o abre dominios fuente."]


def _chart_missing_data(
    *,
    series: list[AssistantChartSeries],
    vitals: list[VitalSign],
    exam_events: list[ClinicalEvent],
) -> list[str]:
    missing = []
    if not vitals:
        missing.append("No hay signos vitales estructurados para graficar.")
    if not exam_events:
        missing.append("No hay eventos exam_result estructurados para graficar.")
    if not series:
        missing.append("No hay datos numericos graficables para las series solicitadas.")
    return missing


def _chart_warnings(*, selected: set[str], has_more: bool, limit: int) -> list[str]:
    warnings = []
    unsupported = sorted(
        series
        for series in selected
        if series not in VITAL_CHART_SERIES
        and series != "exam_result"
        and not series.startswith("exam:")
    )
    if unsupported:
        warnings.append(f"Series no soportadas: {', '.join(unsupported)}.")
    if has_more:
        warnings.append(f"Datos graficables limitados a {limit} registros por dominio.")
    return warnings


def _match_columns(pattern: str, *columns: object):
    return or_(*(column.ilike(pattern, escape="\\") for column in columns))


def _like_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _matched_fields(query: str, fields: dict[str, str | None]) -> list[str]:
    normalized_query = _normalize_for_match(query)
    matches = [
        name
        for name, value in fields.items()
        if value and normalized_query in _normalize_for_match(value)
    ]
    return matches or ["summary"]


def _snippet(query: str, *values: str | None) -> str:
    normalized_query = _normalize_for_match(query)
    texts = [_collapse(value) for value in values if value]
    for text in texts:
        if normalized_query in _normalize_for_match(text):
            return _truncate(text)
    return _truncate(" / ".join(texts) or "Resultado clinico estructurado")


def _collapse(value: str) -> str:
    return " ".join(value.split())


def _normalize_for_match(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(character for character in decomposed if not combining(character))


def _normalize_series_key(value: str) -> str:
    return _normalize_for_match(value.strip()).replace(" ", "_")


def _numeric_value(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _truncate(value: str, max_length: int = 320) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."
