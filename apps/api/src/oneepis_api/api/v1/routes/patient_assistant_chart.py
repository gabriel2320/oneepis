from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from oneepis_api.api.deps import PatientReadActorDep
from oneepis_api.models.clinical_record import (
    ClinicalEvent,
    ClinicalEventType,
    RecordStatus,
    VitalSign,
)
from oneepis_api.schemas.clinical_record import (
    AssistantChartPoint,
    AssistantChartRequest,
    AssistantChartResponse,
    AssistantChartSeries,
)

from .patient_assistant_common import VITAL_CHART_SERIES, normalize_series_key, numeric_value
from .patient_assistant_labs import exam_chart_series, fetch_lab_results_for_assistant
from .patient_shared import SessionDep, record_patient_scoped_read, require_patient

router = APIRouter()


@router.post("/{patient_id}/assistant/chart", response_model=AssistantChartResponse)
def get_assistant_chart_data(
    patient_id: uuid.UUID,
    payload: AssistantChartRequest,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> AssistantChartResponse:
    require_patient(session, patient_id)
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=actor,
        action="assistant_chart.read",
    )
    selected = {normalize_series_key(series) for series in payload.series if series.strip()}
    query_limit = payload.limit + 1
    vitals = list(
        session.scalars(
            select(VitalSign)
            .where(
                VitalSign.patient_id == patient_id,
                VitalSign.status != RecordStatus.ENTERED_IN_ERROR,
            )
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
    lab_results = fetch_lab_results_for_assistant(session, patient_id, query_limit)
    series = [
        *_vital_chart_series(patient_id, list(reversed(vitals)), selected),
        *exam_chart_series(
            patient_id,
            list(reversed(lab_results)),
            list(reversed(exam_events)),
            selected,
        ),
    ]
    has_more = (
        len(vitals) > payload.limit
        or len(exam_events) > payload.limit
        or len(lab_results) > payload.limit
    )
    return AssistantChartResponse(
        patient_id=patient_id,
        series=series,
        missing_data=_chart_missing_data(
            series=series,
            vitals=vitals,
            exam_events=exam_events,
            lab_results=lab_results,
        ),
        warnings=_chart_warnings(
            selected=selected,
            has_more=has_more,
            limit=payload.limit,
        ),
        limit=payload.limit,
        has_more=has_more,
    )


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
            if (value := numeric_value(getattr(vital, attribute))) is not None
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


def _chart_missing_data(
    *,
    series: list[AssistantChartSeries],
    vitals: list[VitalSign],
    exam_events: list[ClinicalEvent],
    lab_results: list[object],
) -> list[str]:
    missing = []
    if not vitals:
        missing.append("No hay signos vitales estructurados para graficar.")
    if not exam_events and not lab_results:
        missing.append("No hay examenes estructurados ni eventos exam_result para graficar.")
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
