from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.clinical_record import (
    ClinicalChangeSet,
    ClinicalIntentRequest,
    ClinicalIntentResponse,
    ClinicalIntentRouteRequest,
    ClinicalIntentRouteResponse,
    ClinicalReviewItem,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_intent_actions import (
    clinical_intent_action as _action,
)
from oneepis_api.services.clinical_intent_change_rules import (
    event_rule_findings as _event_rule_findings,
)
from oneepis_api.services.clinical_intent_change_rules import (
    vital_rule_findings as _vital_rule_findings,
)
from oneepis_api.services.clinical_intent_context import (
    clinical_intent_context_payload as _context_payload,
)
from oneepis_api.services.clinical_intent_exam_rules import (
    exam_payload_rule_findings as _exam_payload_rule_findings,
)
from oneepis_api.services.clinical_intent_medication_rules import (
    medication_payload_rule_findings as _medication_payload_rule_findings,
)
from oneepis_api.services.clinical_intent_medication_rules import (
    medication_review_findings as _medication_review_findings,
)
from oneepis_api.services.clinical_intent_review import (
    apply_review_decisions as _apply_review_decisions,
)
from oneepis_api.services.clinical_intent_review import (
    build_review_items as _review_items,
)
from oneepis_api.services.clinical_intent_router import (
    route_clinical_intent as _route_clinical_intent,
)
from oneepis_api.services.clinical_intent_text import join_titles as _join_titles
from oneepis_api.services.clinical_lab_context import fetch_context_lab_results


def route_clinical_intent(payload: ClinicalIntentRouteRequest) -> ClinicalIntentRouteResponse:
    return _route_clinical_intent(payload)


def resolve_clinical_intent(
    session: Session,
    patient_id: uuid.UUID,
    payload: ClinicalIntentRequest,
) -> ClinicalIntentResponse:
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
    events = patient_repo.get_recent_events(session, patient_id, limit=payload.max_events)
    recent_vitals = patient_repo.get_recent_vitals(session, patient_id, limit=2)
    lab_results = fetch_context_lab_results(session, patient_id)
    latest_entry = snapshot.recent_entries[0] if snapshot.recent_entries else None
    review_items = _review_items(snapshot, events, latest_entry)
    review_items = _apply_review_decisions(session, patient_id, review_items)

    if payload.intent_type == "summarize_patient":
        return _summarize_patient(
            payload, snapshot, events, recent_vitals, lab_results, review_items
        )
    if payload.intent_type == "daily_changes":
        return _daily_changes(payload, snapshot, events, recent_vitals, lab_results, review_items)
    if payload.intent_type == "active_problems":
        return _active_problems(payload, snapshot, recent_vitals, lab_results, review_items)
    if payload.intent_type == "timeline":
        return _timeline(payload, snapshot, events, recent_vitals, lab_results, review_items)
    if payload.intent_type == "draft_soap":
        return _draft_soap_intent(
            payload, snapshot, events, recent_vitals, lab_results, review_items
        )
    return _show_sources(payload, snapshot, events, recent_vitals, lab_results, review_items)


def _summarize_patient(
    payload: ClinicalIntentRequest,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    recent_vitals: list[object],
    lab_results: list[object],
    review_items: list[ClinicalReviewItem],
) -> ClinicalIntentResponse:
    patient = snapshot.patient
    lines = [
        f"{patient.first_name} {patient.last_name}.",
        f"Estado: {patient.clinical_status}; contexto: {patient.current_care_context}.",
        "Problemas activos: "
        f"{_join_titles([problem.title for problem in snapshot.active_problems])}.",
        f"Medicacion activa: {_join_titles([med.name for med in snapshot.active_medications])}.",
        f"Eventos recientes: {_join_titles([event.summary for event in events[:5]])}.",
    ]
    return ClinicalIntentResponse(
        intent_type=payload.intent_type,
        mode=payload.mode,
        clinical_answer="\n".join(lines),
        **_context_payload(snapshot, events, lab_results),
        certainty="moderate" if events or snapshot.recent_entries else "low",
        change_set=_change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[
            _action(
                "create_soap_draft",
                "Preparar evolucion SOAP",
                "Crear un borrador editable desde el contexto construido.",
                requires_confirmation=True,
            ),
            _action("review_sources", "Mostrar fuentes", "Revisar la evidencia usada."),
        ],
    )


def _daily_changes(
    payload: ClinicalIntentRequest,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    recent_vitals: list[object],
    lab_results: list[object],
    review_items: list[ClinicalReviewItem],
) -> ClinicalIntentResponse:
    latest_entry = snapshot.recent_entries[0] if snapshot.recent_entries else None
    event_lines = [f"- {event.summary}" for event in events[:8]]
    rule_findings = _vital_rule_findings(recent_vitals)
    event_lines.extend(f"- Regla: {finding}" for finding in rule_findings)
    if latest_entry:
        event_lines.append(f"- Ultima evolucion: {latest_entry.title}")
    answer = "\n".join(event_lines) if event_lines else "No hay eventos recientes suficientes."
    return ClinicalIntentResponse(
        intent_type=payload.intent_type,
        mode=payload.mode,
        clinical_answer=answer,
        **_context_payload(snapshot, events, lab_results),
        certainty="moderate" if event_lines else "low",
        change_set=_change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[
            _action(
                "add_pending",
                "Agregar pendiente",
                "Crear una propuesta revisable para seguimiento clinico.",
                requires_confirmation=True,
            )
        ],
    )


def _active_problems(
    payload: ClinicalIntentRequest,
    snapshot: PatientRecordSnapshot,
    recent_vitals: list[object],
    lab_results: list[object],
    review_items: list[ClinicalReviewItem],
) -> ClinicalIntentResponse:
    if snapshot.active_problems:
        answer = "\n".join(
            f"{index}. {problem.title} - {problem.notes or 'sin nota de plan'}"
            for index, problem in enumerate(snapshot.active_problems, start=1)
        )
    else:
        answer = "No hay problemas activos registrados."
    missing = []
    if not snapshot.active_problems:
        missing.append("Problemas activos estructurados")
    return ClinicalIntentResponse(
        intent_type=payload.intent_type,
        mode=payload.mode,
        clinical_answer=answer,
        **_context_payload(snapshot, [], lab_results, missing_data=missing),
        certainty="high" if snapshot.active_problems else "low",
        change_set=_change_set(snapshot, [], recent_vitals),
        review_items=review_items,
        proposed_actions=[
            _action(
                "create_event",
                "Registrar problema",
                "Crear propuesta estructurada; no escribir sin confirmacion.",
                requires_confirmation=True,
            )
        ],
    )


def _timeline(
    payload: ClinicalIntentRequest,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    recent_vitals: list[object],
    lab_results: list[object],
    review_items: list[ClinicalReviewItem],
) -> ClinicalIntentResponse:
    items = [f"- {event.occurred_at.isoformat()}: {event.summary}" for event in events[:10]]
    items.extend(
        f"- {entry.occurred_at.isoformat()}: {entry.title}" for entry in snapshot.recent_entries[:5]
    )
    return ClinicalIntentResponse(
        intent_type=payload.intent_type,
        mode=payload.mode,
        clinical_answer="\n".join(items) if items else "No hay timeline suficiente.",
        **_context_payload(snapshot, events, lab_results),
        certainty="moderate" if items else "low",
        change_set=_change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[
            _action("review_sources", "Revisar fuentes", "Abrir fuentes del timeline construido.")
        ],
    )


def _draft_soap_intent(
    payload: ClinicalIntentRequest,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    recent_vitals: list[object],
    lab_results: list[object],
    review_items: list[ClinicalReviewItem],
) -> ClinicalIntentResponse:
    subjective = _join_titles([event.summary for event in events[:5]])
    objective = "Sin signos vitales recientes."
    if snapshot.latest_vitals:
        vital = snapshot.latest_vitals
        objective = (
            f"FC {vital.heart_rate_bpm or '-'}, "
            f"PA {vital.systolic_bp or '-'}/{vital.diastolic_bp or '-'}, "
            f"Sat {vital.oxygen_saturation_pct or '-'}."
        )
    answer = "\n".join(
        [
            "S:",
            subjective,
            "O:",
            objective,
            "A:",
            _join_titles([problem.title for problem in snapshot.active_problems])
            or "En evaluacion.",
            "P:",
            "Completar plan, revisar fuentes y confirmar antes de guardar.",
        ]
    )
    return ClinicalIntentResponse(
        intent_type=payload.intent_type,
        mode="draft",
        clinical_answer=answer,
        **_context_payload(snapshot, events, lab_results),
        certainty="moderate" if events else "low",
        change_set=_change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[
            _action(
                "create_soap_draft",
                "Guardar borrador SOAP",
                "Guardar como borrador no firmado tras revision humana.",
                requires_confirmation=True,
            )
        ],
        warnings=["Borrador no firmado. Requiere revision humana."],
        requires_human_confirmation=True,
    )


def _show_sources(
    payload: ClinicalIntentRequest,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    recent_vitals: list[object],
    lab_results: list[object],
    review_items: list[ClinicalReviewItem],
) -> ClinicalIntentResponse:
    context_payload = _context_payload(snapshot, events, lab_results, missing_data=[])
    sources = context_payload["sources"]
    return ClinicalIntentResponse(
        intent_type=payload.intent_type,
        mode=payload.mode,
        clinical_answer="\n".join(f"- {source.label}" for source in sources) or "Sin fuentes.",
        **context_payload,
        certainty="high" if sources else "low",
        change_set=_change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[_action("none", "Sin accion", "Lectura solamente.")],
    )


def _change_set(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    recent_vitals: list[object],
) -> ClinicalChangeSet:
    latest_entry = snapshot.recent_entries[0] if snapshot.recent_entries else None
    missing = []
    if latest_entry is None:
        missing.append("Evolucion previa para comparar")
    if not events:
        missing.append("Eventos nuevos para comparar")
    if len(recent_vitals) < 2:
        missing.append("Dos controles de signos vitales para comparar")
    rule_findings = [
        *_vital_rule_findings(recent_vitals),
        *_event_rule_findings(snapshot, events, latest_entry, recent_vitals),
        *_exam_payload_rule_findings(events, latest_entry),
        *_medication_payload_rule_findings(events, latest_entry),
        *_medication_review_findings(snapshot, events, latest_entry),
    ]
    return ClinicalChangeSet(
        baseline=latest_entry.title if latest_entry else None,
        new_items=[event.summary for event in events[:8]],
        rule_findings=rule_findings,
        missing_for_comparison=missing,
    )
