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
    Medication,
    RecordStatus,
    VitalSign,
)
from oneepis_api.models.hospitalization import HospitalIndication
from oneepis_api.schemas.assistant import AssistantTimelineItem, AssistantTimelineResponse


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


def _sort_key(item: AssistantTimelineItem) -> datetime:
    if item.occurred_at is not None:
        return _aware_datetime(item.occurred_at)
    if item.occurred_on is not None:
        return datetime.combine(item.occurred_on, time.min, tzinfo=UTC)
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


def _code_label(system: str | None, code: str | None) -> str | None:
    if not system or not code:
        return None
    return f"{system}: {code}"


def _compact(values: list[Any]) -> list[str]:
    return [str(value).strip() for value in values if str(value or "").strip()]
