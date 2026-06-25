from __future__ import annotations

import uuid
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

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
from oneepis_api.models.hospitalization import HospitalIndication
from oneepis_api.schemas.assistant import (
    AssistantChartMetric,
    AssistantChartPoint,
    AssistantChartRequest,
    AssistantChartResponse,
    AssistantChartSeries,
    AssistantCorrelationFinding,
    AssistantCorrelationPreset,
    AssistantCorrelationRequest,
    AssistantCorrelationResponse,
    AssistantSearchMatch,
    AssistantSearchRequest,
    AssistantSearchResponse,
    AssistantTimelineItem,
    AssistantTimelineResponse,
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
DEFAULT_CORRELATION_PRESETS: tuple[AssistantCorrelationPreset, ...] = (
    "fever_infection",
    "renal_medications",
    "respiratory_oxygen",
    "hemoglobin_bleeding",
    "medication_changes",
)


def build_assistant_timeline(
    session: Session,
    patient_id: uuid.UUID,
    *,
    limit: int = 100,
) -> AssistantTimelineResponse:
    items = [
        *_encounter_items(_list_encounters(session, patient_id, limit)),
        *_entry_items(_list_entries(session, patient_id, limit)),
        *_event_items(_list_events(session, patient_id, limit)),
        *_vital_items(_list_vitals(session, patient_id, limit)),
        *_problem_items(_list_active_problems(session, patient_id)),
        *_medication_items(_list_active_medications(session, patient_id)),
        *_allergy_items(_list_active_allergies(session, patient_id)),
        *_hospital_indication_items(_list_hospital_indications(session, patient_id, limit)),
    ]
    items.sort(key=_sort_key, reverse=True)
    limited_items = items[:limit]
    missing = _missing_domains(
        entries=items,
        source_types={item.source_type for item in items},
    )
    limits = [
        "Timeline deterministico de solo lectura; no diagnostica ni prescribe.",
        "Medicamentos, problemas y alergias se limitan a registros activos.",
        f"Respuesta limitada a {limit} item(s) ordenados por fecha disponible.",
    ]
    return AssistantTimelineResponse(
        patient_id=patient_id,
        items=limited_items,
        missing=missing,
        limits=limits,
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


def build_assistant_correlations(
    session: Session,
    patient_id: uuid.UUID,
    payload: AssistantCorrelationRequest,
) -> AssistantCorrelationResponse:
    presets = _unique_presets(payload.presets or list(DEFAULT_CORRELATION_PRESETS))
    timeline = build_assistant_timeline(session, patient_id, limit=100)
    findings: list[AssistantCorrelationFinding] = []
    missing: list[str] = []

    for preset in presets:
        finding = _correlate_preset(preset, timeline.items, payload.limit)
        if finding is None:
            missing.append(_correlation_missing_message(preset))
            continue
        findings.append(finding)

    return AssistantCorrelationResponse(
        patient_id=patient_id,
        findings=findings[: payload.limit],
        missing=missing,
        limits=[
            "Correlacion deterministica de solo lectura; no diagnostica ni prescribe.",
            "Solo relaciona fuentes existentes por presets cerrados y texto estructurado.",
            f"Respuesta limitada a {payload.limit} hallazgo(s).",
        ],
    )


def search_assistant_timeline(
    session: Session,
    patient_id: uuid.UUID,
    payload: AssistantSearchRequest,
) -> AssistantSearchResponse:
    timeline = build_assistant_timeline(session, patient_id, limit=100)
    allowed_source_types = set(payload.source_types)
    query = payload.query.strip()
    normalized_query = _normalize_text(query)
    matches: list[AssistantSearchMatch] = []

    for item in timeline.items:
        if allowed_source_types and item.source_type not in allowed_source_types:
            continue
        matched_fields, snippets = _match_item(item, normalized_query)
        if not matched_fields:
            continue
        matches.append(
            AssistantSearchMatch(
                item=item,
                matched_fields=matched_fields,
                snippets=snippets,
            )
        )
        if len(matches) >= payload.limit:
            break

    searched_source_types = payload.source_types or sorted(
        {item.source_type for item in timeline.items}
    )
    return AssistantSearchResponse(
        patient_id=patient_id,
        query=query,
        matches=matches,
        searched_source_types=searched_source_types,
        limits=[
            "Busqueda deterministica de solo lectura sobre fuentes normalizadas del timeline.",
            "No usa embeddings, RAG ni IA generativa; "
            "puede omitir sinonimos o negaciones complejas.",
            f"Respuesta limitada a {payload.limit} coincidencia(s).",
        ],
    )


def _unique_metrics(metrics: list[AssistantChartMetric]) -> list[AssistantChartMetric]:
    unique: list[AssistantChartMetric] = []
    for metric in metrics:
        if metric not in unique:
            unique.append(metric)
    return unique


def _unique_presets(
    presets: list[AssistantCorrelationPreset],
) -> list[AssistantCorrelationPreset]:
    unique: list[AssistantCorrelationPreset] = []
    for preset in presets:
        if preset not in unique:
            unique.append(preset)
    return unique


def _list_encounters(
    session: Session,
    patient_id: uuid.UUID,
    limit: int,
) -> list[ClinicalEncounter]:
    return list(
        session.scalars(
            select(ClinicalEncounter)
            .where(ClinicalEncounter.patient_id == patient_id)
            .order_by(ClinicalEncounter.started_at.desc())
            .limit(limit)
        )
    )


def _list_entries(session: Session, patient_id: uuid.UUID, limit: int) -> list[ClinicalEntry]:
    return list(
        session.scalars(
            select(ClinicalEntry)
            .where(ClinicalEntry.patient_id == patient_id)
            .order_by(ClinicalEntry.occurred_at.desc())
            .limit(limit)
        )
    )


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


def _list_active_problems(session: Session, patient_id: uuid.UUID) -> list[ActiveProblem]:
    return list(
        session.scalars(
            select(ActiveProblem)
            .where(
                ActiveProblem.patient_id == patient_id,
                ActiveProblem.status == RecordStatus.ACTIVE,
            )
            .order_by(ActiveProblem.created_at.desc())
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


def _list_active_allergies(session: Session, patient_id: uuid.UUID) -> list[Allergy]:
    return list(
        session.scalars(
            select(Allergy)
            .where(Allergy.patient_id == patient_id, Allergy.status == RecordStatus.ACTIVE)
            .order_by(Allergy.recorded_at.desc())
        )
    )


def _list_hospital_indications(
    session: Session,
    patient_id: uuid.UUID,
    limit: int,
) -> list[HospitalIndication]:
    return list(
        session.scalars(
            select(HospitalIndication)
            .where(HospitalIndication.patient_id == patient_id)
            .order_by(HospitalIndication.indicated_at.desc())
            .limit(limit)
        )
    )


def _encounter_items(encounters: list[ClinicalEncounter]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="encounter",
            source_id=encounter.id,
            patient_id=encounter.patient_id,
            encounter_id=encounter.id,
            occurred_at=encounter.started_at,
            label=f"Encuentro {encounter.type.value}",
            summary=encounter.reason,
            status=encounter.status.value,
            details=_compact([encounter.location_label, encounter.notes]),
        )
        for encounter in encounters
    ]


def _entry_items(entries: list[ClinicalEntry]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="clinical_entry",
            source_id=entry.id,
            patient_id=entry.patient_id,
            encounter_id=entry.encounter_id,
            occurred_at=entry.occurred_at,
            label=entry.title,
            summary=_join_sections(entry),
            status=entry.status.value,
            details=[f"Tipo: {entry.kind.value}"],
            payload={"tags": entry.tags},
        )
        for entry in entries
    ]


def _event_items(events: list[ClinicalEvent]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="clinical_event",
            source_id=event.id,
            patient_id=event.patient_id,
            encounter_id=event.encounter_id,
            occurred_at=event.occurred_at,
            label=f"Evento {event.event_type.value}",
            summary=event.summary,
            status=event.source_type.value,
            source_ref=event.source_ref,
            payload=event.payload,
        )
        for event in events
    ]


def _vital_items(vitals: list[VitalSign]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="vital_sign",
            source_id=vital.id,
            patient_id=vital.patient_id,
            occurred_at=vital.measured_at,
            label="Signos vitales",
            summary=_vital_summary(vital),
            details=_compact([vital.notes]),
        )
        for vital in vitals
    ]


def _problem_items(problems: list[ActiveProblem]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="active_problem",
            source_id=problem.id,
            patient_id=problem.patient_id,
            occurred_on=problem.onset_date,
            label=problem.title,
            summary=problem.notes or "Problema activo sin nota adicional.",
            status=problem.status.value,
            details=_compact([_code_label(problem.code_system, problem.code)]),
        )
        for problem in problems
    ]


def _medication_items(medications: list[Medication]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="medication",
            source_id=medication.id,
            patient_id=medication.patient_id,
            occurred_on=medication.started_on,
            label=medication.name,
            summary=_medication_summary(medication),
            status=medication.status.value,
        )
        for medication in medications
    ]


def _allergy_items(allergies: list[Allergy]) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="allergy",
            source_id=allergy.id,
            patient_id=allergy.patient_id,
            occurred_at=allergy.recorded_at,
            label=allergy.substance,
            summary=allergy.reaction or "Alergia registrada sin reaccion documentada.",
            status=allergy.severity.value,
        )
        for allergy in allergies
    ]


def _hospital_indication_items(
    indications: list[HospitalIndication],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            source_type="hospital_indication",
            source_id=indication.id,
            patient_id=indication.patient_id,
            encounter_id=indication.encounter_id,
            occurred_at=indication.indicated_at,
            label=indication.title,
            summary=indication.indication_text,
            status=indication.status.value,
            details=_compact([indication.rationale, indication.safety_notes]),
        )
        for indication in indications
    ]


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


def _correlate_preset(
    preset: AssistantCorrelationPreset,
    items: list[AssistantTimelineItem],
    limit: int,
) -> AssistantCorrelationFinding | None:
    if preset == "fever_infection":
        fever = _filter_items(items, keywords=("fiebre", "febril", "temperatura"))
        fever.extend(
            item
            for item in items
            if item.source_type == "vital_sign"
            and _payload_or_summary_has_temperature(item, minimum=38.0)
            and item not in fever
        )
        infection = _filter_items(
            items,
            keywords=(
                "infecc",
                "pcr",
                "proteina c reactiva",
                "leucoc",
                "cultivo",
                "antibiot",
            ),
        )
        return _finding_if_sources(
            preset=preset,
            title="Fiebre e infeccion",
            summary=(
                "Fuentes con fiebre o temperatura elevada aparecen junto a fuentes "
                "infecciosas o inflamatorias."
            ),
            groups=[fever, infection],
            missing=["Faltan fiebre documentada.", "Faltan fuentes infecciosas o inflamatorias."],
            limit=limit,
        )

    if preset == "renal_medications":
        renal = _filter_items(
            items,
            keywords=("renal", "creatinina", "clearance", "egfr", "filtrado glomerular"),
        )
        medications = [item for item in items if item.source_type == "medication"]
        return _finding_if_sources(
            preset=preset,
            title="Funcion renal y medicamentos",
            summary="Fuentes renales aparecen junto a medicacion activa registrada.",
            groups=[renal, medications],
            missing=["Faltan fuentes renales.", "Falta medicacion activa."],
            limit=limit,
        )

    if preset == "respiratory_oxygen":
        respiratory = _filter_items(
            items,
            keywords=("disnea", "respiratorio", "sato2", "saturacion", "hipox", "fr "),
        )
        respiratory.extend(
            item
            for item in items
            if item.source_type == "vital_sign"
            and (_payload_or_summary_has_saturation(item, maximum=92.0) or "FR " in item.summary)
            and item not in respiratory
        )
        oxygen = _filter_items(items, keywords=("oxigen", "naricera", "fio2", "ventil"))
        return _finding_if_sources(
            preset=preset,
            title="Respiratorio y oxigeno",
            summary=(
                "Fuentes respiratorias o de saturacion baja aparecen junto a registros "
                "de oxigeno o soporte ventilatorio."
            ),
            groups=[respiratory, oxygen],
            missing=[
                "Faltan fuentes respiratorias.",
                "Faltan fuentes de oxigeno o soporte ventilatorio.",
            ],
            limit=limit,
        )

    if preset == "hemoglobin_bleeding":
        hemoglobin = _filter_items(
            items,
            keywords=("hemoglobina", "hematocrito", " hb ", "anemia"),
        )
        bleeding = _filter_items(
            items,
            keywords=("sangrado", "hemorrag", "melena", "hematemesis", "rectorragia"),
        )
        return _finding_if_sources(
            preset=preset,
            title="Hemoglobina y sangrado",
            summary=(
                "Fuentes hematologicas aparecen junto a registros compatibles con "
                "sangrado documentado."
            ),
            groups=[hemoglobin, bleeding],
            missing=["Faltan fuentes de hemoglobina o hematocrito.", "Faltan fuentes de sangrado."],
            limit=limit,
        )

    medication_items = [item for item in items if item.source_type == "medication"]
    medication_events = [
        item
        for item in _filter_items(items, keywords=("inicia", "suspende", "ajusta", "cambia"))
        if item.source_type in {"clinical_event", "clinical_entry", "medication"}
    ]
    sources = _dedupe_items([*medication_events, *medication_items])[:limit]
    if len(sources) < 2:
        return None
    return AssistantCorrelationFinding(
        preset="medication_changes",
        title="Cambios de medicacion",
        summary=(
            "Hay multiples fuentes de medicacion o cambios narrativos que conviene "
            "revisar en orden temporal."
        ),
        sources=sources,
        missing=[],
    )


def _finding_if_sources(
    *,
    preset: AssistantCorrelationPreset,
    title: str,
    summary: str,
    groups: list[list[AssistantTimelineItem]],
    missing: list[str],
    limit: int,
) -> AssistantCorrelationFinding | None:
    present_groups = [group for group in groups if group]
    if len(present_groups) != len(groups):
        return None
    sources = _dedupe_items([item for group in groups for item in group])[:limit]
    return AssistantCorrelationFinding(
        preset=preset,
        title=title,
        summary=summary,
        sources=sources,
        missing=[] if sources else missing,
    )


def _filter_items(
    items: list[AssistantTimelineItem],
    *,
    keywords: tuple[str, ...],
) -> list[AssistantTimelineItem]:
    normalized_keywords = tuple(_normalize_text(keyword) for keyword in keywords)
    matches = []
    for item in items:
        haystack = _normalize_text(
            " ".join(
                _compact(
                    [
                        item.label,
                        item.summary,
                        item.status,
                        " ".join(item.details),
                        _payload_text(item.payload),
                    ]
                )
            )
        )
        if any(keyword in haystack for keyword in normalized_keywords):
            matches.append(item)
    return matches


def _dedupe_items(items: list[AssistantTimelineItem]) -> list[AssistantTimelineItem]:
    seen: set[tuple[str, uuid.UUID]] = set()
    unique = []
    for item in items:
        key = (item.source_type, item.source_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    unique.sort(key=_sort_key, reverse=True)
    return unique


def _payload_or_summary_has_temperature(
    item: AssistantTimelineItem,
    *,
    minimum: float,
) -> bool:
    value = _payload_number(item.payload)
    if value is not None and value >= minimum:
        return True
    summary_value = _number_after_label(item.summary, "T")
    return summary_value is not None and summary_value >= minimum


def _payload_or_summary_has_saturation(
    item: AssistantTimelineItem,
    *,
    maximum: float,
) -> bool:
    value = _payload_number(item.payload)
    if value is not None and value <= maximum:
        return True
    summary_value = _number_after_label(item.summary, "SatO2")
    return summary_value is not None and summary_value <= maximum


def _number_after_label(value: str, label: str) -> float | None:
    marker = f"{label} "
    if marker not in value:
        return None
    tail = value.split(marker, 1)[1].split(" ", 1)[0].replace(",", ".")
    try:
        return float(tail)
    except ValueError:
        return None


def _correlation_missing_message(preset: AssistantCorrelationPreset) -> str:
    messages = {
        "fever_infection": "No hay suficientes fuentes para correlacionar fiebre e infeccion.",
        "renal_medications": (
            "No hay suficientes fuentes para correlacionar funcion renal y medicamentos."
        ),
        "respiratory_oxygen": (
            "No hay suficientes fuentes para correlacionar respiratorio y oxigeno."
        ),
        "hemoglobin_bleeding": (
            "No hay suficientes fuentes para correlacionar hemoglobina y sangrado."
        ),
        "medication_changes": (
            "No hay suficientes fuentes para correlacionar cambios de medicacion."
        ),
    }
    return messages[preset]


def _sort_key(item: AssistantTimelineItem) -> datetime:
    if item.occurred_at is not None:
        return _aware_datetime(item.occurred_at)
    if item.occurred_on is not None:
        return datetime.combine(item.occurred_on, time.min, tzinfo=UTC)
    return datetime.min.replace(tzinfo=UTC)


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


def _missing_domains(
    *,
    entries: list[AssistantTimelineItem],
    source_types: set[str],
) -> list[str]:
    missing = []
    expected = {
        "encounter": "No hay encuentros clinicos para ordenar el episodio.",
        "clinical_entry": "No hay evoluciones o documentos narrativos en el timeline.",
        "clinical_event": "No hay eventos longitudinales estructurados.",
        "vital_sign": "No hay signos vitales recientes.",
        "active_problem": "No hay problemas activos registrados.",
        "medication": "No hay medicacion activa registrada.",
        "allergy": "No hay alergias activas registradas.",
        "hospital_indication": "No hay indicaciones hospitalarias registradas.",
    }
    for source_type, message in expected.items():
        if source_type not in source_types:
            missing.append(message)
    if not entries:
        missing.append("La historia longitudinal no tiene fuentes disponibles para este paciente.")
    return missing


def _join_sections(entry: ClinicalEntry) -> str:
    sections = _compact([entry.subjective, entry.objective, entry.assessment, entry.plan])
    return " | ".join(sections) if sections else "Entrada clinica sin secciones SOAP documentadas."


def _vital_summary(vital: VitalSign) -> str:
    values = _compact(
        [
            _format_decimal("T", vital.temperature_c, "C"),
            _blood_pressure(vital.systolic_bp, vital.diastolic_bp),
            _format_int("FC", vital.heart_rate_bpm, "lpm"),
            _format_int("FR", vital.respiratory_rate_bpm, "rpm"),
            _format_decimal("SatO2", vital.oxygen_saturation_pct, "%"),
        ]
    )
    return ", ".join(values) if values else "Control de signos vitales sin valores numericos."


def _medication_summary(medication: Medication) -> str:
    values = _compact([medication.dose, medication.route, medication.frequency])
    return " - ".join(values) if values else "Medicacion activa sin posologia estructurada."


def _blood_pressure(systolic: int | None, diastolic: int | None) -> str | None:
    if systolic is None or diastolic is None:
        return None
    return f"PA {systolic}/{diastolic} mmHg"


def _format_int(label: str, value: int | None, unit: str) -> str | None:
    if value is None:
        return None
    return f"{label} {value} {unit}"


def _format_decimal(label: str, value: Decimal | None, unit: str) -> str | None:
    if value is None:
        return None
    return f"{label} {value.normalize()} {unit}"


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


def _code_label(system: str | None, code: str | None) -> str | None:
    if not system or not code:
        return None
    return f"{system}: {code}"


def _compact(values: list[Any]) -> list[str]:
    return [str(value).strip() for value in values if str(value or "").strip()]


def _match_item(item: AssistantTimelineItem, normalized_query: str) -> tuple[list[str], list[str]]:
    searchable_fields = {
        "label": item.label,
        "summary": item.summary,
        "status": item.status,
        "details": " ".join(item.details),
        "source_ref": item.source_ref,
        "payload": _payload_text(item.payload),
    }
    matched_fields: list[str] = []
    snippets: list[str] = []
    for field, raw_value in searchable_fields.items():
        value = str(raw_value or "").strip()
        if not value:
            continue
        if normalized_query not in _normalize_text(value):
            continue
        matched_fields.append(field)
        snippets.append(_snippet(value, normalized_query))
    return matched_fields, snippets[:3]


def _payload_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in payload.items():
        if isinstance(value, dict):
            parts.append(_payload_text(value))
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        else:
            parts.append(f"{key}: {value}")
    return " ".join(_compact(parts))


def _normalize_text(value: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "Á": "a",
            "É": "e",
            "Í": "i",
            "Ó": "o",
            "Ú": "u",
            "ñ": "n",
            "Ñ": "n",
        }
    )
    return value.translate(replacements).casefold()


def _snippet(value: str, normalized_query: str) -> str:
    normalized_value = _normalize_text(value)
    index = normalized_value.find(normalized_query)
    if index < 0:
        return value[:160]
    start = max(index - 50, 0)
    end = min(index + len(normalized_query) + 80, len(value))
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(value) else ""
    return f"{prefix}{value[start:end]}{suffix}"
