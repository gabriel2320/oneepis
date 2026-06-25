from __future__ import annotations

import uuid
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import (
    ClinicalEvent,
    ClinicalEventType,
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.schemas.assistant import (
    AssistantChartMetric,
    AssistantChartPoint,
    AssistantChartRequest,
    AssistantChartResponse,
    AssistantChartSeries,
)

VITAL_CHART_FIELDS: dict[str, tuple[str, str, str]] = {
    "temperature_c": ("temperature_c", "Temperatura", "C"),
    "systolic_bp": ("systolic_bp", "Presion sistolica", "mmHg"),
    "diastolic_bp": ("diastolic_bp", "Presion diastolica", "mmHg"),
    "heart_rate_bpm": ("heart_rate_bpm", "Frecuencia cardiaca", "lpm"),
    "respiratory_rate_bpm": ("respiratory_rate_bpm", "Frecuencia respiratoria", "rpm"),
    "oxygen_saturation_pct": ("oxygen_saturation_pct", "Saturacion de oxigeno", "%"),
}
DEFAULT_CHART_METRICS: tuple[AssistantChartMetric, ...] = (
    "temperature_c",
    "systolic_bp",
    "diastolic_bp",
    "heart_rate_bpm",
    "respiratory_rate_bpm",
    "oxygen_saturation_pct",
    "exam_result",
    "medication",
)


def build_assistant_chart(
    session: Session,
    patient_id: uuid.UUID,
    payload: AssistantChartRequest,
) -> AssistantChartResponse:
    metrics = _unique_metrics(payload.metrics or list(DEFAULT_CHART_METRICS))
    series: list[AssistantChartSeries] = []
    missing: list[str] = []

    vital_metrics = [metric for metric in metrics if metric in VITAL_CHART_FIELDS]
    if vital_metrics:
        vitals = _list_vitals(session, patient_id, payload.limit)
        for metric in vital_metrics:
            chart_series = _vital_chart_series(metric, vitals)
            if chart_series.points:
                series.append(chart_series)
        if not any(item.key in vital_metrics for item in series):
            missing.append("No hay signos vitales con valores graficables.")

    if "exam_result" in metrics:
        exam_series = _exam_result_chart_series(_list_events(session, patient_id, payload.limit))
        if exam_series.points:
            series.append(exam_series)
        else:
            missing.append("No hay eventos exam_result con valores graficables.")

    if "medication" in metrics:
        medication_series = _medication_chart_series(
            _list_active_medications(session, patient_id)
        )
        if medication_series.points:
            series.append(medication_series)
        else:
            missing.append("No hay medicacion activa con fecha de inicio.")

    return AssistantChartResponse(
        patient_id=patient_id,
        series=series,
        missing=missing,
        limits=[
            "Datos graficables de solo lectura; no diagnostican ni prescriben.",
            "Examenes se leen solo desde eventos clinical_event con event_type exam_result.",
            f"Respuesta limitada a {payload.limit} registro(s) por fuente consultada.",
        ],
    )


def _unique_metrics(metrics: list[AssistantChartMetric]) -> list[AssistantChartMetric]:
    unique: list[AssistantChartMetric] = []
    for metric in metrics:
        if metric not in unique:
            unique.append(metric)
    return unique


def _list_events(session: Session, patient_id: uuid.UUID, limit: int) -> list[ClinicalEvent]:
    return list(
        session.scalars(
            select(ClinicalEvent)
            .where(ClinicalEvent.patient_id == patient_id)
            .order_by(ClinicalEvent.occurred_at.desc())
            .limit(limit)
        )
    )


def _list_vitals(session: Session, patient_id: uuid.UUID, limit: int) -> list[VitalSign]:
    return list(
        session.scalars(
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
            .order_by(VitalSign.measured_at.desc())
            .limit(limit)
        )
    )


def _list_active_medications(session: Session, patient_id: uuid.UUID) -> list[Medication]:
    return list(
        session.scalars(
            select(Medication)
            .where(Medication.patient_id == patient_id, Medication.status == RecordStatus.ACTIVE)
            .order_by(Medication.started_on.desc().nullslast(), Medication.created_at.desc())
        )
    )


def _vital_chart_series(
    metric: AssistantChartMetric,
    vitals: list[VitalSign],
) -> AssistantChartSeries:
    attr, label, unit = VITAL_CHART_FIELDS[str(metric)]
    points = [
        AssistantChartPoint(
            source_type="vital_sign",
            source_id=vital.id,
            occurred_at=vital.measured_at,
            label=label,
            value=_to_float(getattr(vital, attr)),
            unit=unit,
            payload={"notes": vital.notes} if vital.notes else {},
        )
        for vital in vitals
        if getattr(vital, attr) is not None
    ]
    points.sort(key=_chart_sort_key)
    return AssistantChartSeries(key=metric, label=label, unit=unit, points=points)


def _exam_result_chart_series(events: list[ClinicalEvent]) -> AssistantChartSeries:
    points = []
    for event in events:
        if event.event_type != ClinicalEventType.EXAM_RESULT:
            continue
        points.append(
            AssistantChartPoint(
                source_type="clinical_event",
                source_id=event.id,
                encounter_id=event.encounter_id,
                occurred_at=event.occurred_at,
                label=_exam_label(event),
                value=_payload_number(event.payload),
                unit=_payload_unit(event.payload),
                payload=event.payload,
            )
        )
    points.sort(key=_chart_sort_key)
    return AssistantChartSeries(key="exam_result", label="Examenes", unit=None, points=points)


def _medication_chart_series(medications: list[Medication]) -> AssistantChartSeries:
    points = [
        AssistantChartPoint(
            source_type="medication",
            source_id=medication.id,
            occurred_on=medication.started_on,
            label=medication.name,
            value=1.0,
            unit=None,
            payload={
                "dose": medication.dose,
                "route": medication.route,
                "frequency": medication.frequency,
                "status": medication.status.value,
            },
        )
        for medication in medications
        if medication.started_on is not None
    ]
    points.sort(key=_chart_sort_key)
    return AssistantChartSeries(
        key="medication",
        label="Medicacion activa",
        unit=None,
        points=points,
    )


def _chart_sort_key(point: AssistantChartPoint) -> datetime:
    if point.occurred_at is not None:
        return _aware_datetime(point.occurred_at)
    if point.occurred_on is not None:
        return datetime.combine(point.occurred_on, time.min, tzinfo=UTC)
    return datetime.min.replace(tzinfo=UTC)


def _aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _to_float(value: Decimal | int | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _exam_label(event: ClinicalEvent) -> str:
    for key in ("marker", "test", "name", "analyte"):
        value = str(event.payload.get(key) or "").strip()
        if value:
            return value[:160]
    return event.summary


def _payload_number(payload: dict[str, Any]) -> float | None:
    for key in ("value", "result", "numeric_value"):
        value = payload.get(key)
        if isinstance(value, Decimal | int | float):
            return float(value)
        if isinstance(value, str):
            normalized = value.strip().replace(",", ".")
            try:
                return float(normalized)
            except ValueError:
                continue
    return None


def _payload_unit(payload: dict[str, Any]) -> str | None:
    unit = str(payload.get("unit") or "").strip()
    return unit[:40] if unit else None
