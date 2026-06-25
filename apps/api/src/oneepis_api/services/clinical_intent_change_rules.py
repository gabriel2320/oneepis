from __future__ import annotations

from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_course import clinical_course_finding
from oneepis_api.services.clinical_intent_text import compare_decimal as _compare_decimal
from oneepis_api.services.clinical_intent_text import compare_int as _compare_int
from oneepis_api.services.clinical_problem_context import event_matches_any_problem


def vital_rule_findings(recent_vitals: list[object]) -> list[str]:
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


def event_rule_findings(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    baseline_entry: object | None,
    recent_vitals: list[object],
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
        course_finding = clinical_course_finding(event.summary, recent_vitals)
        if course_finding:
            findings.append(course_finding)

    unlinked_count = sum(
        1 for event in compared_events if not event_matches_any_problem(snapshot, event)
    )
    if unlinked_count:
        findings.append(
            f"{unlinked_count} evento(s) recientes sin problema activo asociado."
        )
    return findings
