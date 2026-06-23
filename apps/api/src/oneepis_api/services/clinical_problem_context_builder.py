from __future__ import annotations

import uuid

from oneepis_api.schemas.clinical_record import ClinicalEvidenceMark, ClinicalProblemContext
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_lab_context import problem_lab_evidence
from oneepis_api.services.clinical_problem_context import (
    problem_domain_label,
    problem_domain_missing_data,
    problem_event_match_reason,
)


def build_problem_contexts(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    lab_results: list[object],
) -> list[ClinicalProblemContext]:
    contexts: list[ClinicalProblemContext] = []
    linked_event_ids: set[uuid.UUID] = set()

    for problem in snapshot.active_problems[:8]:
        event_reasons = [
            (event, reason)
            for event in events
            if (reason := problem_event_match_reason(problem, event))
        ]
        matched_events = [event for event, _reason in event_reasons]
        linked_event_ids.update(event.id for event in matched_events)
        lab_evidence = problem_lab_evidence(problem, lab_results)
        evidence = [
            ClinicalEvidenceMark(
                label=event.summary,
                status="confirmed",
                detail=reason,
                source_id=event.id,
            )
            for event, reason in event_reasons[:5]
        ]
        evidence.extend(lab_evidence[: max(0, 5 - len(evidence))])
        pending = []
        if not evidence:
            pending.append("Sin evidencia reciente asociada automaticamente.")
        if not problem.notes:
            pending.append("Problema sin nota de plan estructurada.")
        pending.extend(problem_domain_missing_data(problem, snapshot, events, lab_results))
        contexts.append(
            ClinicalProblemContext(
                problem_id=problem.id,
                title=problem.title,
                status="structured",
                evidence=evidence,
                pending=pending,
                explanations=_problem_explanations(problem, evidence, lab_evidence),
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
                    "Estos eventos recientes no coincidieron con reglas locales "
                    "de problemas activos.",
                    "Se muestran como contexto no vinculado para revision humana.",
                ],
            )
        )
    return contexts


def _problem_explanations(
    problem: object,
    evidence: list[ClinicalEvidenceMark],
    lab_evidence: list[ClinicalEvidenceMark],
) -> list[str]:
    explanations = [
        "Problema activo estructurado en la ficha.",
        (
            "La evidencia se asocia por codigo SNOMED CT externo, coincidencia textual "
            "o vocabulario clinico local explicito."
        ),
    ]
    domain = problem_domain_label(problem)
    if domain:
        explanations.append(f"Dominio clinico probable para faltantes contextuales: {domain}.")
    if evidence:
        explanations.append(f"{len(evidence)} evidencia(s) reciente(s) vinculadas por regla local.")
    if lab_evidence:
        explanations.append(f"{len(lab_evidence)} resultado(s) estructurado(s) aportan contexto.")
    else:
        explanations.append("No hubo coincidencia ni vocabulario local con eventos recientes.")
    if problem.notes:
        explanations.append("El problema tiene nota de plan estructurada.")
    else:
        explanations.append("Falta nota de plan; se mantiene pendiente de revision.")
    return explanations
