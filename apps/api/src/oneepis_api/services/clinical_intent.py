from __future__ import annotations

import uuid
from unicodedata import category, normalize

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.models.audit import AuditEvent
from oneepis_api.repositories import patients as patient_repo
from oneepis_api.schemas.clinical_record import (
    ClinicalChangeSet,
    ClinicalContextSection,
    ClinicalEvidenceMark,
    ClinicalIntentAction,
    ClinicalIntentRequest,
    ClinicalIntentResponse,
    ClinicalIntentRouteRequest,
    ClinicalIntentRouteResponse,
    ClinicalIntentSource,
    ClinicalIntentType,
    ClinicalProblemContext,
    ClinicalReviewItem,
)
from oneepis_api.schemas.patient import PatientRecordSnapshot

ReviewDecisionMetadata = dict[str, object]


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
    latest_entry = snapshot.recent_entries[0] if snapshot.recent_entries else None
    review_items = _review_items(snapshot, events, latest_entry)
    review_items = _apply_review_decisions(session, patient_id, review_items)

    if payload.intent_type == "summarize_patient":
        return _summarize_patient(payload, snapshot, events, recent_vitals, review_items)
    if payload.intent_type == "daily_changes":
        return _daily_changes(payload, snapshot, events, recent_vitals, review_items)
    if payload.intent_type == "active_problems":
        return _active_problems(payload, snapshot, recent_vitals, review_items)
    if payload.intent_type == "timeline":
        return _timeline(payload, snapshot, events, recent_vitals, review_items)
    if payload.intent_type == "draft_soap":
        return _draft_soap_intent(payload, snapshot, events, recent_vitals, review_items)
    return _show_sources(payload, snapshot, events, recent_vitals, review_items)


def route_clinical_intent(payload: ClinicalIntentRouteRequest) -> ClinicalIntentRouteResponse:
    text = _normalize_text(payload.text)
    direct_action = _direct_form_action(text, payload.text)
    if direct_action:
        return ClinicalIntentRouteResponse(
            recognized=True,
            original_text=payload.text,
            intent_type=None,
            mode="structured_proposal",
            confidence="moderate",
            explanation=(
                "Se reconocio una accion de registro. AI-Chart abrira un formulario existente; "
                "no se guardaran datos sin revision humana."
            ),
            suggested_actions=[direct_action],
            fallback_options=_fallback_actions(),
        )

    matches: list[tuple[ClinicalIntentType, str, tuple[str, ...]]] = [
        (
            "draft_soap",
            "draft",
            (
                "evolucion",
                "evoluciona",
                "soap",
                "nota de hoy",
                "prepara evolucion",
            ),
        ),
        (
            "daily_changes",
            "read",
            (
                "cambio",
                "cambios",
                "desde ayer",
                "ultimas 24",
                "24h",
                "24 horas",
            ),
        ),
        (
            "active_problems",
            "read",
            (
                "problemas",
                "diagnosticos activos",
                "problemas activos",
                "ordena problemas",
            ),
        ),
        (
            "timeline",
            "read",
            (
                "timeline",
                "linea de tiempo",
                "hospitalizacion",
                "cronologia",
            ),
        ),
        (
            "show_sources",
            "read",
            (
                "fuentes",
                "de donde",
                "auditoria",
                "trazabilidad",
            ),
        ),
        (
            "summarize_patient",
            "read",
            (
                "resume",
                "resumen",
                "ordename",
                "ordename",
                "caso",
                "paciente",
            ),
        ),
    ]
    for intent_type, mode, keywords in matches:
        if any(keyword in text for keyword in keywords):
            return ClinicalIntentRouteResponse(
                recognized=True,
                original_text=payload.text,
                intent_type=intent_type,
                mode=mode,
                confidence="high",
                explanation="Intencion reconocida por router clinico deterministico.",
                suggested_actions=[
                    _action(
                        "create_soap_draft"
                        if intent_type == "draft_soap"
                        else "review_sources",
                        _intent_label(intent_type),
                        "Ejecutar la intencion reconocida como accion revisable.",
                        requires_confirmation=intent_type == "draft_soap",
                    )
                ],
                fallback_options=_fallback_actions(),
            )

    return ClinicalIntentRouteResponse(
        recognized=False,
        original_text=payload.text,
        intent_type=None,
        mode="read",
        confidence="low",
        explanation="No se reconocio una intencion clinica segura. Elige una opcion dirigida.",
        suggested_actions=[],
        fallback_options=_fallback_actions(),
    )


def _summarize_patient(
    payload: ClinicalIntentRequest,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    recent_vitals: list[object],
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
        sources=_sources(snapshot, events),
        certainty="moderate" if events or snapshot.recent_entries else "low",
        missing_data=_missing_data(snapshot, events),
        evidence_marks=_evidence_marks(snapshot, events),
        context_sections=_context_sections(snapshot, events),
        problem_contexts=_problem_contexts(snapshot, events),
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
        sources=_sources(snapshot, events),
        certainty="moderate" if event_lines else "low",
        missing_data=_missing_data(snapshot, events),
        evidence_marks=_evidence_marks(snapshot, events),
        context_sections=_context_sections(snapshot, events),
        problem_contexts=_problem_contexts(snapshot, events),
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
        sources=_sources(snapshot, []),
        certainty="high" if snapshot.active_problems else "low",
        missing_data=missing,
        evidence_marks=_evidence_marks(snapshot, []),
        context_sections=_context_sections(snapshot, []),
        problem_contexts=_problem_contexts(snapshot, []),
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
        sources=_sources(snapshot, events),
        certainty="moderate" if items else "low",
        missing_data=_missing_data(snapshot, events),
        evidence_marks=_evidence_marks(snapshot, events),
        context_sections=_context_sections(snapshot, events),
        problem_contexts=_problem_contexts(snapshot, events),
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
        sources=_sources(snapshot, events),
        certainty="moderate" if events else "low",
        missing_data=_missing_data(snapshot, events),
        evidence_marks=_evidence_marks(snapshot, events),
        context_sections=_context_sections(snapshot, events),
        problem_contexts=_problem_contexts(snapshot, events),
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
    review_items: list[ClinicalReviewItem],
) -> ClinicalIntentResponse:
    sources = _sources(snapshot, events)
    return ClinicalIntentResponse(
        intent_type=payload.intent_type,
        mode=payload.mode,
        clinical_answer="\n".join(f"- {source.label}" for source in sources) or "Sin fuentes.",
        sources=sources,
        certainty="high" if sources else "low",
        missing_data=[],
        evidence_marks=_evidence_marks(snapshot, events),
        context_sections=_context_sections(snapshot, events),
        problem_contexts=_problem_contexts(snapshot, events),
        change_set=_change_set(snapshot, events, recent_vitals),
        review_items=review_items,
        proposed_actions=[_action("none", "Sin accion", "Lectura solamente.")],
    )


def _sources(snapshot: PatientRecordSnapshot, events: list[object]) -> list[ClinicalIntentSource]:
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


def _missing_data(snapshot: PatientRecordSnapshot, events: list[object]) -> list[str]:
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


def _evidence_marks(
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


def _context_sections(
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


def _problem_contexts(
    snapshot: PatientRecordSnapshot,
    events: list[object],
) -> list[ClinicalProblemContext]:
    contexts: list[ClinicalProblemContext] = []
    linked_event_ids: set[uuid.UUID] = set()

    for problem in snapshot.active_problems[:8]:
        title = problem.title
        matched_events = [
            event
            for event in events
            if title.casefold() in event.summary.casefold()
            or event.summary.casefold() in title.casefold()
        ]
        linked_event_ids.update(event.id for event in matched_events)
        evidence = [
            ClinicalEvidenceMark(
                label=event.summary,
                status="confirmed",
                detail="Evento reciente asociado por coincidencia textual con el problema.",
                source_id=event.id,
            )
            for event in matched_events[:5]
        ]
        pending = []
        if not evidence:
            pending.append("Sin evidencia reciente asociada automaticamente.")
        if not problem.notes:
            pending.append("Problema sin nota de plan estructurada.")
        explanations = [
            "Problema activo estructurado en la ficha.",
            "La evidencia se asocia cuando el texto del evento y el titulo del problema coinciden.",
        ]
        if evidence:
            explanations.append(
                f"{len(evidence)} evento(s) reciente(s) vinculados por coincidencia textual."
            )
        else:
            explanations.append("No hubo coincidencia textual con eventos recientes.")
        if problem.notes:
            explanations.append("El problema tiene nota de plan estructurada.")
        else:
            explanations.append("Falta nota de plan; se mantiene pendiente de revision.")
        contexts.append(
            ClinicalProblemContext(
                problem_id=problem.id,
                title=title,
                status="structured",
                evidence=evidence,
                pending=pending,
                explanations=explanations,
            )
        )

    unlinked_events = [event for event in events[:8] if event.id not in linked_event_ids]
    if unlinked_events:
        contexts.append(
            ClinicalProblemContext(
                title="Eventos sin problema asociado",
                status="unlinked",
                evidence=[
                    ClinicalEvidenceMark(
                        label=event.summary,
                        status="needs_review",
                        detail="Evento reciente aun no vinculado a un problema activo.",
                        source_id=event.id,
                    )
                    for event in unlinked_events
                ],
                pending=["Revisar si corresponde crear o actualizar un problema activo."],
                explanations=[
                    "Estos eventos recientes no coincidieron textualmente con problemas activos.",
                    "Se muestran como contexto no vinculado para revision humana.",
                ],
            )
        )
    return contexts


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
        *_event_rule_findings(snapshot, events, latest_entry),
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


def _vital_rule_findings(recent_vitals: list[object]) -> list[str]:
    if len(recent_vitals) < 2:
        return []
    current = recent_vitals[0]
    previous = recent_vitals[1]
    findings: list[str] = []
    findings.extend(
        _compare_decimal(
            label="Temperatura",
            current=current.temperature_c,
            previous=previous.temperature_c,
            unit="C",
            relevant_delta=0.5,
        )
    )
    findings.extend(
        _compare_int(
            label="Frecuencia cardiaca",
            current=current.heart_rate_bpm,
            previous=previous.heart_rate_bpm,
            unit="lpm",
            relevant_delta=15,
        )
    )
    findings.extend(
        _compare_int(
            label="Presion sistolica",
            current=current.systolic_bp,
            previous=previous.systolic_bp,
            unit="mmHg",
            relevant_delta=20,
        )
    )
    findings.extend(
        _compare_decimal(
            label="Saturacion O2",
            current=current.oxygen_saturation_pct,
            previous=previous.oxygen_saturation_pct,
            unit="%",
            relevant_delta=2,
        )
    )
    return findings


def _event_rule_findings(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    baseline_entry: object | None,
) -> list[str]:
    compared_events = [
        event
        for event in events[:12]
        if baseline_entry is None or event.occurred_at > baseline_entry.occurred_at
    ]
    if not compared_events:
        return []

    findings: list[str] = []
    labels = {
        "exam_result": "Nuevo examen registrado",
        "medication": "Nuevo evento de medicacion registrado",
        "care_plan": "Nuevo plan de cuidado registrado",
        "diagnosis": "Nuevo diagnostico registrado",
        "procedure": "Nuevo procedimiento registrado",
    }
    for event in compared_events:
        event_type = getattr(event.event_type, "value", event.event_type)
        label = labels.get(event_type)
        if label:
            findings.append(f"{label}: {event.summary}.")

    unlinked_count = sum(
        1 for event in compared_events if not _event_matches_any_problem(snapshot, event)
    )
    if unlinked_count:
        findings.append(
            f"{unlinked_count} evento(s) recientes sin problema activo asociado."
        )
    return findings


def _event_matches_any_problem(snapshot: PatientRecordSnapshot, event: object) -> bool:
    summary = event.summary.casefold()
    return any(
        problem.title.casefold() in summary or summary in problem.title.casefold()
        for problem in snapshot.active_problems
    )


def _exam_payload_rule_findings(
    events: list[object],
    baseline_entry: object | None,
) -> list[str]:
    findings: list[str] = []
    grouped: dict[str, list[tuple[object, dict[str, object]]]] = {}
    for event in events:
        event_type = getattr(event.event_type, "value", event.event_type)
        if event_type != "exam_result":
            continue
        for result in _exam_results(event.payload):
            marker = _exam_marker(result)
            value = _exam_value(result)
            if marker is None or value is None:
                continue
            grouped.setdefault(marker, []).append((event, result))

    for marker, marker_results in grouped.items():
        ordered = sorted(marker_results, key=lambda item: item[0].occurred_at, reverse=True)
        if len(ordered) < 2:
            continue
        current, current_result = ordered[0]
        previous, previous_result = ordered[1]
        if baseline_entry is not None and current.occurred_at <= baseline_entry.occurred_at:
            continue
        current_value = _exam_value(current_result)
        previous_value = _exam_value(previous_result)
        if current_value is None or previous_value is None:
            continue
        finding = _exam_delta_finding(
            marker=marker,
            current=current_value,
            previous=previous_value,
            unit=str(current_result.get("unit") or previous_result.get("unit") or ""),
        )
        if finding:
            findings.append(finding)
    return findings


def _exam_results(payload: dict[str, object]) -> list[dict[str, object]]:
    raw_results = payload.get("results")
    if isinstance(raw_results, list):
        return [item for item in raw_results if isinstance(item, dict)]
    return [payload]


def _exam_marker(payload: dict[str, object]) -> str | None:
    raw = payload.get("code") or payload.get("name") or payload.get("marker")
    if not isinstance(raw, str):
        return None
    normalized = _normalize_text(raw).replace("_", " ").strip()
    aliases = {
        "pcr": "pcr",
        "proteina c reactiva": "pcr",
        "crp": "pcr",
        "creatinina": "creatinine",
        "creatinine": "creatinine",
        "hemoglobina": "hemoglobin",
        "hemoglobin": "hemoglobin",
        "hb": "hemoglobin",
    }
    return aliases.get(normalized)


def _exam_value(payload: dict[str, object]) -> float | None:
    raw = payload.get("value")
    if isinstance(raw, int | float):
        return float(raw)
    if isinstance(raw, str):
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            return None
    return None


def _exam_delta_finding(
    *,
    marker: str,
    current: float,
    previous: float,
    unit: str,
) -> str | None:
    labels = {
        "pcr": "PCR",
        "creatinine": "Creatinina",
        "hemoglobin": "Hemoglobina",
    }
    thresholds = {
        "pcr": max(abs(previous) * 0.3, 10),
        "creatinine": 0.3,
        "hemoglobin": 1.0,
    }
    delta = current - previous
    if abs(delta) < thresholds[marker]:
        return None
    direction = "subio" if delta > 0 else "bajo"
    suffix = f" {unit}" if unit else ""
    return f"{labels[marker]} {direction} de {previous:g} a {current:g}{suffix}."


def _medication_payload_rule_findings(
    events: list[object],
    baseline_entry: object | None,
) -> list[str]:
    findings: list[str] = []
    for event in events:
        event_type = getattr(event.event_type, "value", event.event_type)
        if event_type != "medication":
            continue
        if baseline_entry is not None and event.occurred_at <= baseline_entry.occurred_at:
            continue
        finding = _medication_payload_finding(event.payload)
        if finding:
            findings.append(finding)
    return findings


def _medication_review_findings(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    baseline_entry: object | None,
) -> list[str]:
    findings: list[str] = []
    for medication in snapshot.active_medications[:12]:
        if not medication.dose:
            findings.append(f"Revisar medicamento activo sin dosis: {medication.name}.")
        if not medication.frequency:
            findings.append(f"Revisar medicamento activo sin frecuencia: {medication.name}.")

    compared_med_events = [
        event
        for event in events[:12]
        if getattr(event.event_type, "value", event.event_type) == "medication"
        and (baseline_entry is None or event.occurred_at > baseline_entry.occurred_at)
    ]
    for event in compared_med_events:
        if not _medication_payload_has_minimum(event.payload):
            findings.append(
                f"Revisar evento de medicacion sin payload estructurado suficiente: "
                f"{event.summary}."
            )
        if not _event_matches_any_problem(snapshot, event):
            findings.append(
                f"Revisar evento de medicacion sin problema activo asociado: {event.summary}."
            )
    return findings


def _review_items(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    baseline_entry: object | None,
) -> list[ClinicalReviewItem]:
    items: list[ClinicalReviewItem] = []
    for medication in snapshot.active_medications[:12]:
        if not medication.dose:
            items.append(
                ClinicalReviewItem(
                    item_type="missing_medication_dose",
                    label=f"{medication.name}: falta dosis",
                    detail="Medicamento activo sin dosis estructurada.",
                    source_type="medication",
                    source_id=medication.id,
                    suggested_action="Completar dosis o confirmar que no aplica.",
                )
            )
        if not medication.frequency:
            items.append(
                ClinicalReviewItem(
                    item_type="missing_medication_frequency",
                    label=f"{medication.name}: falta frecuencia",
                    detail="Medicamento activo sin frecuencia estructurada.",
                    source_type="medication",
                    source_id=medication.id,
                    suggested_action="Completar frecuencia o confirmar que no aplica.",
                )
            )

    compared_med_events = [
        event
        for event in events[:12]
        if getattr(event.event_type, "value", event.event_type) == "medication"
        and (baseline_entry is None or event.occurred_at > baseline_entry.occurred_at)
    ]
    for event in compared_med_events:
        if not _medication_payload_has_minimum(event.payload):
            items.append(
                ClinicalReviewItem(
                    item_type="unstructured_medication_event",
                    label="Evento de medicacion incompleto",
                    detail=event.summary,
                    source_type="clinical_event",
                    source_id=event.id,
                    suggested_action="Completar payload con action y name/medication.",
                )
            )
        if not _event_matches_any_problem(snapshot, event):
            items.append(
                ClinicalReviewItem(
                    item_type="unlinked_medication_event",
                    label="Evento de medicacion sin problema asociado",
                    detail=event.summary,
                    source_type="clinical_event",
                    source_id=event.id,
                    suggested_action="Vincular a un problema activo o crear uno si corresponde.",
                )
            )
    return items


def _apply_review_decisions(
    session: Session,
    patient_id: uuid.UUID,
    items: list[ClinicalReviewItem],
) -> list[ClinicalReviewItem]:
    if not items:
        return items
    decisions = _review_decision_map(session, patient_id)
    if not decisions:
        return items
    applied: list[ClinicalReviewItem] = []
    for item in items:
        key = _review_item_key(
            item_type=item.item_type,
            source_type=item.source_type,
            source_id=item.source_id,
            label=item.label,
        )
        decision = decisions.get(key)
        if decision:
            item = item.model_copy(
                update={
                    "decision_status": decision["status"],
                    "decision_actor_id": decision["actor_id"],
                    "decision_at": decision["created_at"],
                    "decision_audit_event_id": decision["audit_event_id"],
                }
            )
        applied.append(item)
    return applied


def _review_decision_map(
    session: Session,
    patient_id: uuid.UUID,
) -> dict[str, ReviewDecisionMetadata]:
    statement = (
        select(AuditEvent)
        .where(
            AuditEvent.action == "ai.review_item.decided",
            AuditEvent.entity_type == "patient",
            AuditEvent.entity_id == patient_id,
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(100)
    )
    decisions: dict[str, ReviewDecisionMetadata] = {}
    for audit_event in session.scalars(statement):
        metadata = audit_event.extra_data
        decision = metadata.get("decision")
        if decision not in {"accepted", "rejected"}:
            continue
        key = _review_item_key(
            item_type=str(metadata.get("item_type") or ""),
            source_type=str(metadata.get("source_type") or ""),
            source_id=metadata.get("source_id"),
            label=str(metadata.get("label") or ""),
        )
        decisions.setdefault(
            key,
            {
                "status": decision,
                "actor_id": audit_event.actor_id,
                "created_at": audit_event.created_at,
                "audit_event_id": audit_event.id,
            },
        )
    return decisions


def _review_item_key(
    *,
    item_type: str,
    source_type: str,
    source_id: uuid.UUID | str | None,
    label: str,
) -> str:
    return "|".join([item_type, source_type, str(source_id or ""), label])


def _medication_payload_has_minimum(payload: dict[str, object]) -> bool:
    return _payload_text(payload.get("action")) is not None and (
        _payload_text(payload.get("name")) is not None
        or _payload_text(payload.get("medication")) is not None
    )


def _medication_payload_finding(payload: dict[str, object]) -> str | None:
    action_raw = payload.get("action")
    name_raw = payload.get("name") or payload.get("medication")
    if not isinstance(action_raw, str) or not isinstance(name_raw, str):
        return None
    action = _normalize_text(action_raw).replace("_", "-").strip()
    name = name_raw.strip()
    if not name:
        return None

    if action in {"started", "iniciado", "inicio"}:
        detail = _medication_detail(payload)
        return f"Medicamento iniciado: {name}{detail}."
    if action in {"stopped", "suspended", "suspendido", "suspension"}:
        return f"Medicamento suspendido: {name}."
    if action in {"dose-changed", "dose changed", "cambio dosis", "ajuste dosis"}:
        previous_dose = _payload_text(payload.get("previous_dose"))
        dose = _payload_text(payload.get("dose"))
        if previous_dose and dose:
            return f"Dosis modificada: {name} de {previous_dose} a {dose}."
        if dose:
            return f"Dosis modificada: {name} a {dose}."
    return None


def _medication_detail(payload: dict[str, object]) -> str:
    dose = _payload_text(payload.get("dose"))
    route = _payload_text(payload.get("route"))
    frequency = _payload_text(payload.get("frequency"))
    details = [item for item in [dose, route, frequency] if item]
    return f" ({', '.join(details)})" if details else ""


def _payload_text(value: object | None) -> str | None:
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    if isinstance(value, int | float):
        return str(value)
    return None


def _compare_int(
    *,
    label: str,
    current: int | None,
    previous: int | None,
    unit: str,
    relevant_delta: int,
) -> list[str]:
    if current is None or previous is None:
        return []
    delta = current - previous
    if abs(delta) < relevant_delta:
        return []
    direction = "subio" if delta > 0 else "bajo"
    return [f"{label} {direction} de {previous} a {current} {unit}."]


def _compare_decimal(
    *,
    label: str,
    current: object | None,
    previous: object | None,
    unit: str,
    relevant_delta: float,
) -> list[str]:
    if current is None or previous is None:
        return []
    current_value = float(current)
    previous_value = float(previous)
    delta = current_value - previous_value
    if abs(delta) < relevant_delta:
        return []
    direction = "subio" if delta > 0 else "bajo"
    return [f"{label} {direction} de {previous_value:g} a {current_value:g} {unit}."]


def _join_titles(values: list[str]) -> str:
    return ", ".join(values[:6]) if values else "sin registros"


def _normalize_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if category(char) != "Mn")


def _intent_label(intent_type: ClinicalIntentType) -> str:
    labels = {
        "summarize_patient": "Resumir paciente",
        "daily_changes": "Comparar ultimas 24 h",
        "active_problems": "Mostrar problemas activos",
        "timeline": "Crear timeline",
        "draft_soap": "Preparar evolucion S/O/A/P",
        "show_sources": "Mostrar fuentes",
    }
    return labels[intent_type]


def _fallback_actions() -> list[ClinicalIntentAction]:
    return [
        _action("review_sources", "Resumir paciente", "Ver contexto clinico resumido."),
        _action("review_sources", "Que cambio desde ayer", "Comparar cambios recientes."),
        _action(
            "create_soap_draft",
            "Preparar evolucion SOAP",
            "Crear borrador editable con confirmacion humana.",
            requires_confirmation=True,
        ),
        _action("review_sources", "Mostrar fuentes", "Ver fuentes usadas por AI-Chart."),
    ]


def _direct_form_action(text: str, original_text: str) -> ClinicalIntentAction | None:
    form_actions: list[tuple[tuple[str, ...], str, str]] = [
        (
            ("medicacion", "medicamento", "farmaco", "receta"),
            "Registrar medicacion",
            "Abrir formulario de medicacion con origen AI-Chart revisable.",
        ),
        (
            ("alergia", "alergias", "alergico"),
            "Registrar alergia",
            "Abrir formulario de alergias con origen AI-Chart revisable.",
        ),
        (
            ("signos vitales", "control de signos", "presion", "saturacion", "temperatura"),
            "Registrar signos vitales",
            "Abrir formulario de signos vitales con origen AI-Chart revisable.",
        ),
    ]
    for keywords, label, description in form_actions:
        if any(keyword in text for keyword in keywords):
            return _action(
                "create_event",
                label,
                f"{description} Texto original: {original_text}",
                requires_confirmation=True,
            )
    return None


def _action(
    action_type: str,
    label: str,
    description: str,
    *,
    requires_confirmation: bool = False,
) -> ClinicalIntentAction:
    return ClinicalIntentAction(
        action_type=action_type,
        action_id=f"{action_type}:{_normalize_text(label).replace(' ', '_')}",
        label=label,
        description=description,
        confirmation_label="Revisar y confirmar" if requires_confirmation else "Revisar",
        requires_confirmation=requires_confirmation,
    )
