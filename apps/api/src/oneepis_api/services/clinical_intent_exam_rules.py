from __future__ import annotations

from oneepis_api.services.clinical_intent_text import normalize_text as _normalize_text


def exam_payload_rule_findings(
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
        _previous, previous_result = ordered[1]
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
