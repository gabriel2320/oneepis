from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import ClinicalEvent
from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.clinical_record import (
    ClinicalContextSection,
    ClinicalEvidenceMark,
    ClinicalIntentSource,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot


@dataclass(frozen=True)
class ClinicalEventContext:
    snapshot: PatientRecordSnapshot
    events: list[ClinicalEvent]


def build_event_context(
    session: Session,
    patient_id: uuid.UUID,
    event_ids: list[uuid.UUID],
) -> ClinicalEventContext:
    patient = patient_repo.get_patient(session, patient_id)
    if patient is None:
        raise ValueError("Patient not found")

    snapshot = PatientRecordSnapshot(
        patient=patient,
        latest_vitals=patient_repo.get_latest_vitals(session, patient_id),
        active_allergies=patient_repo.get_active_allergies(session, patient_id),
        active_medications=patient_repo.get_active_medications(session, patient_id),
        active_problems=patient_repo.get_active_problems(session, patient_id),
        recent_entries=patient_repo.get_recent_entries(session, patient_id),
    )
    events = list(
        session.scalars(
            select(ClinicalEvent).where(
                ClinicalEvent.patient_id == patient_id,
                ClinicalEvent.id.in_(event_ids),
            )
        )
    )
    events.sort(key=lambda item: item.occurred_at)
    return ClinicalEventContext(snapshot=snapshot, events=events)


def clinical_sources(
    snapshot: PatientRecordSnapshot,
    events: list[object],
) -> list[ClinicalIntentSource]:
    sources = [
        ClinicalIntentSource(
            source_type="clinical_event",
            source_id=event.id,
            label=event.summary,
        )
        for event in events[:10]
    ]
    sources.extend(
        ClinicalIntentSource(
            source_type="clinical_entry",
            source_id=entry.id,
            label=entry.title,
        )
        for entry in snapshot.recent_entries[:5]
    )
    if snapshot.latest_vitals:
        sources.append(
            ClinicalIntentSource(
                source_type="vital_sign",
                source_id=snapshot.latest_vitals.id,
                label="Ultimos signos vitales",
            )
        )
    return sources


def clinical_missing_data(snapshot: PatientRecordSnapshot, events: list[object]) -> list[str]:
    missing: list[str] = []
    care_context = snapshot.patient.current_care_context
    if not events:
        missing.append(
            "Eventos clinicos recientes: necesarios para construir contexto longitudinal."
        )
    if snapshot.latest_vitals is None:
        if care_context == "hospitalized":
            missing.append(
                "Signos vitales recientes: requeridos para contexto hospitalizado."
            )
        else:
            missing.append("Signos vitales recientes: faltan para contexto objetivo.")
    if not snapshot.active_problems:
        missing.append(
            "Problemas activos estructurados: necesarios para agrupar evidencia por problema."
        )
    if not snapshot.recent_entries:
        if care_context == "ambulatory":
            missing.append("Evolucion ambulatoria reciente: falta baseline para comparar control.")
        elif care_context == "hospitalized":
            missing.append("Evolucion u hoja diaria reciente: falta baseline hospitalizado.")
        else:
            missing.append("Evolucion reciente: falta baseline clinico para comparar.")
    return missing


def clinical_evidence_marks(
    snapshot: PatientRecordSnapshot,
    events: list[object],
) -> list[ClinicalEvidenceMark]:
    marks: list[ClinicalEvidenceMark] = []
    marks.extend(
        ClinicalEvidenceMark(
            label=event.summary,
            status="confirmed",
            detail="Evento clinico registrado en la ficha.",
            source_id=event.id,
        )
        for event in events[:8]
    )
    marks.extend(
        ClinicalEvidenceMark(
            label=entry.title,
            status="confirmed",
            detail="Evolucion/documento clinico registrado.",
            source_id=entry.id,
        )
        for entry in snapshot.recent_entries[:3]
    )
    if snapshot.latest_vitals is None:
        marks.append(
            ClinicalEvidenceMark(
                label="Signos vitales recientes",
                status="missing",
                detail="No hay signos vitales recientes en el snapshot.",
            )
        )
    else:
        marks.append(
            ClinicalEvidenceMark(
                label="Signos vitales recientes",
                status="confirmed",
                detail="Disponibles para contexto objetivo.",
                source_id=snapshot.latest_vitals.id,
            )
        )
    if not snapshot.active_problems:
        marks.append(
            ClinicalEvidenceMark(
                label="Problemas activos",
                status="needs_review",
                detail="No hay problemas activos estructurados; revisar antes de documentar.",
            )
        )
    return marks


def clinical_context_sections(
    snapshot: PatientRecordSnapshot,
    events: list[object],
) -> list[ClinicalContextSection]:
    return [
        ClinicalContextSection(
            title="Problemas activos",
            items=[problem.title for problem in snapshot.active_problems[:6]],
        ),
        ClinicalContextSection(
            title="Eventos recientes",
            items=[event.summary for event in events[:6]],
        ),
        ClinicalContextSection(
            title="Medicacion activa",
            items=[med.name for med in snapshot.active_medications[:6]],
        ),
        ClinicalContextSection(
            title="Evoluciones recientes",
            items=[entry.title for entry in snapshot.recent_entries[:5]],
        ),
    ]
