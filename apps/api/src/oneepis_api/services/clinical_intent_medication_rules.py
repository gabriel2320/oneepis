from __future__ import annotations

from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_intent_review import medication_payload_has_minimum
from oneepis_api.services.clinical_intent_text import normalize_text as _normalize_text
from oneepis_api.services.clinical_intent_text import payload_text as _payload_text
from oneepis_api.services.clinical_problem_context import event_matches_any_problem


def medication_payload_rule_findings(
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


def medication_review_findings(
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
        if not medication_payload_has_minimum(event.payload):
            findings.append(
                f"Revisar evento de medicacion sin payload estructurado suficiente: "
                f"{event.summary}."
            )
        if not event_matches_any_problem(snapshot, event):
            findings.append(
                f"Revisar evento de medicacion sin problema activo asociado: {event.summary}."
            )
    return findings


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
