from __future__ import annotations

from unicodedata import category, normalize

from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_course import clinical_course_finding
from oneepis_api.services.clinical_problem_context import event_matches_any_problem


def change_rule_findings(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    baseline_entry: object | None,
    recent_vitals: list[object],
) -> list[str]:
    return [
        *vital_rule_findings(recent_vitals),
        *_event_rule_findings(snapshot, events, baseline_entry, recent_vitals),
        *_exam_payload_rule_findings(events, baseline_entry),
        *_medication_payload_rule_findings(events, baseline_entry),
        *_medication_review_findings(snapshot, events, baseline_entry),
    ]


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


def medication_payload_has_minimum(payload: dict[str, object]) -> bool:
    return _payload_text(payload.get("action")) is not None and (
        _payload_text(payload.get("name")) is not None
        or _payload_text(payload.get("medication")) is not None
    )


def _event_rule_findings(
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


def _normalize_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if category(char) != "Mn")
