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
from oneepis_api.services.clinical_lab_context import (
    lab_context_items,
    lab_evidence_marks,
    lab_sources,
)


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
    lab_results: list[object] | None = None,
    active_risks: list[object] | None = None,
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
    sources.extend(
        ClinicalIntentSource(
            source_type="active_problem",
            source_id=problem.id,
            label=problem.title,
        )
        for problem in snapshot.active_problems[:8]
    )
    sources.extend(
        ClinicalIntentSource(
            source_type="historical_diagnosis",
            source_id=diagnosis.source_event_id,
            label=diagnosis.title,
        )
        for diagnosis in snapshot.historical_diagnoses[:8]
    )
    sources.extend(
        ClinicalIntentSource(
            source_type="allergy",
            source_id=allergy.id,
            label=allergy.substance,
        )
        for allergy in snapshot.active_allergies[:8]
    )
    sources.extend(
        ClinicalIntentSource(
            source_type="medication",
            source_id=medication.id,
            label=medication.name,
        )
        for medication in snapshot.active_medications[:8]
    )
    sources.extend(
        ClinicalIntentSource(
            source_type="clinical_risk",
            source_id=getattr(risk, "id", None),
            label=_risk_label(risk),
        )
        for risk in (active_risks or [])[:8]
    )
    if snapshot.latest_vitals:
        sources.append(
            ClinicalIntentSource(
                source_type="vital_sign",
                source_id=snapshot.latest_vitals.id,
                label="Ultimos signos vitales",
            )
        )
    sources.extend(lab_sources(lab_results or []))
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
    lab_results: list[object] | None = None,
    active_risks: list[object] | None = None,
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
    marks.extend(lab_evidence_marks(lab_results or []))
    marks.extend(
        ClinicalEvidenceMark(
            label=diagnosis.title,
            status="confirmed",
            detail="Diagnostico historico curado; no es problema activo actual.",
            source_id=diagnosis.source_event_id,
        )
        for diagnosis in snapshot.historical_diagnoses[:5]
    )
    marks.extend(
        ClinicalEvidenceMark(
            label=allergy.substance,
            status="confirmed",
            detail="Alergia activa registrada en la ficha.",
            source_id=allergy.id,
        )
        for allergy in snapshot.active_allergies[:5]
    )
    marks.extend(
        ClinicalEvidenceMark(
            label=_risk_label(risk),
            status="needs_review",
            detail="Riesgo activo registrado; requiere accion humana visible.",
            source_id=getattr(risk, "id", None),
        )
        for risk in (active_risks or [])[:5]
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
    lab_results: list[object] | None = None,
    active_risks: list[object] | None = None,
) -> list[ClinicalContextSection]:
    return [
        ClinicalContextSection(
            title="Problemas activos",
            items=[problem.title for problem in snapshot.active_problems[:6]],
        ),
        ClinicalContextSection(
            title="Diagnosticos historicos",
            items=[diagnosis.title for diagnosis in snapshot.historical_diagnoses[:6]],
        ),
        ClinicalContextSection(
            title="Alergias activas",
            items=[allergy.substance for allergy in snapshot.active_allergies[:6]],
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
            title="Riesgos activos",
            items=[_risk_label(risk) for risk in (active_risks or [])[:6]],
        ),
        ClinicalContextSection(
            title="Examenes estructurados",
            items=lab_context_items(lab_results or []),
        ),
        ClinicalContextSection(
            title="Evoluciones recientes",
            items=[entry.title for entry in snapshot.recent_entries[:5]],
        ),
    ]


def _risk_label(risk: object) -> str:
    risk_type = getattr(
        getattr(risk, "risk_type", "riesgo"),
        "value",
        getattr(risk, "risk_type", "riesgo"),
    )
    reason = getattr(risk, "reason", None)
    return f"Riesgo {risk_type}: {reason}" if reason else f"Riesgo {risk_type}"
