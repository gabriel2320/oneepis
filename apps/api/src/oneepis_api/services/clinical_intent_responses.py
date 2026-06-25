from __future__ import annotations

from oneepis_api.schemas.clinical_record import (
    ClinicalChangeSet,
    ClinicalIntentRequest,
    ClinicalIntentResponse,
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
from oneepis_api.services.clinical_intent_text import join_titles as _join_titles


def summarize_patient_response(
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
        change_set=change_set(snapshot, events, recent_vitals),
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


def daily_changes_response(
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
        change_set=change_set(snapshot, events, recent_vitals),
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


def active_problems_response(
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
        change_set=change_set(snapshot, [], recent_vitals),
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


def timeline_response(
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
        change_set=change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[
            _action("review_sources", "Revisar fuentes", "Abrir fuentes del timeline construido.")
        ],
    )


def draft_soap_intent_response(
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
        change_set=change_set(snapshot, events, recent_vitals),
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


def show_sources_response(
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
        change_set=change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[_action("none", "Sin accion", "Lectura solamente.")],
    )


def change_set(
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
