from __future__ import annotations

from unicodedata import category, normalize


def clinical_course_finding(summary: str, recent_vitals: list[object]) -> str | None:
    normalized = _normalize_text(summary)
    if _negates_clinical_course(normalized):
        return None
    domain = _clinical_course_domain_label(normalized)
    domain_detail = f" (dominio {domain})" if domain else ""
    improving_terms = (
        "mejoria",
        "mejora",
        "mejorando",
        "en disminucion",
        "disminuye",
        "cede",
        "controlado",
        "estable",
    )
    worsening_terms = (
        "empeora",
        "empeoramiento",
        "aumenta",
        "aumento",
        "progresion",
        "persiste",
        "sin mejoria",
        "descompensacion",
    )
    if any(term in normalized for term in worsening_terms):
        corroboration = _clinical_course_vital_corroboration("worsening", domain, recent_vitals)
        corroboration_detail = f" {corroboration}" if corroboration else ""
        return (
            f"Empeoramiento clinico sugerido{domain_detail} por evento: "
            f"{summary}.{corroboration_detail}"
        )
    if any(term in normalized for term in improving_terms):
        corroboration = _clinical_course_vital_corroboration("improving", domain, recent_vitals)
        corroboration_detail = f" {corroboration}" if corroboration else ""
        return (
            f"Mejoria clinica sugerida{domain_detail} por evento: "
            f"{summary}.{corroboration_detail}"
        )
    return None


def _negates_clinical_course(normalized_summary: str) -> bool:
    negated_terms = (
        "sin empeoramiento",
        "sin mayor empeoramiento",
        "no empeora",
        "no presenta empeoramiento",
        "niega empeoramiento",
        "descarta empeoramiento",
        "no hay progresion",
        "sin progresion",
        "niega progresion",
    )
    return any(term in normalized_summary for term in negated_terms)


def _clinical_course_domain_label(normalized_summary: str) -> str | None:
    domains = {
        "respiratorio": (
            "disnea",
            "tos",
            "saturacion",
            "oxigeno",
            "respiratorio",
            "broncoespasmo",
            "expectoracion",
        ),
        "dolor": ("dolor", "algia", "colico", "molestia"),
        "infeccioso": (
            "fiebre",
            "febril",
            "temperatura",
            "calofrios",
            "infeccion",
            "pcr",
        ),
        "hemodinamico": (
            "presion",
            "hipotension",
            "hipertension",
            "taquicardia",
            "bradicardia",
        ),
        "metabolico": (
            "glicemia",
            "glucosa",
            "hipoglicemia",
            "hiperglicemia",
            "diabetes",
            "insulina",
        ),
        "digestivo": ("vomito", "nauseas", "diarrea", "abdomen", "abdominal"),
    }
    for label, terms in domains.items():
        if any(term in normalized_summary for term in terms):
            return label
    return None


def _clinical_course_vital_corroboration(
    direction: str,
    domain: str | None,
    recent_vitals: list[object],
) -> str | None:
    if domain is None or len(recent_vitals) < 2:
        return None
    current = recent_vitals[0]
    previous = recent_vitals[1]

    if domain == "respiratorio":
        saturation = _compare_metric_direction(
            label="saturacion O2",
            current=current.oxygen_saturation_pct,
            previous=previous.oxygen_saturation_pct,
            unit="%",
            relevant_delta=2,
            expected_delta="down" if direction == "worsening" else "up",
        )
        respiratory_rate = _compare_metric_direction(
            label="frecuencia respiratoria",
            current=current.respiratory_rate_bpm,
            previous=previous.respiratory_rate_bpm,
            unit="rpm",
            relevant_delta=4,
            expected_delta="up" if direction == "worsening" else "down",
        )
        detail = saturation or respiratory_rate
    elif domain == "infeccioso":
        detail = _compare_metric_direction(
            label="temperatura",
            current=current.temperature_c,
            previous=previous.temperature_c,
            unit="C",
            relevant_delta=0.5,
            expected_delta="up" if direction == "worsening" else "down",
        )
    elif domain == "hemodinamico":
        detail = _compare_metric_direction(
            label="presion sistolica",
            current=current.systolic_bp,
            previous=previous.systolic_bp,
            unit="mmHg",
            relevant_delta=20,
            expected_delta="up" if direction == "worsening" else "down",
        ) or _compare_metric_direction(
            label="frecuencia cardiaca",
            current=current.heart_rate_bpm,
            previous=previous.heart_rate_bpm,
            unit="lpm",
            relevant_delta=15,
            expected_delta="up" if direction == "worsening" else "down",
        )
    else:
        detail = None

    if detail is None:
        return None
    return f"Corroborado por signos vitales: {detail}."


def _compare_metric_direction(
    *,
    label: str,
    current: object | None,
    previous: object | None,
    unit: str,
    relevant_delta: float,
    expected_delta: str,
) -> str | None:
    if current is None or previous is None:
        return None
    current_value = float(current)
    previous_value = float(previous)
    delta = current_value - previous_value
    if abs(delta) < relevant_delta:
        return None
    if expected_delta == "up" and delta <= 0:
        return None
    if expected_delta == "down" and delta >= 0:
        return None
    direction = "subio" if delta > 0 else "bajo"
    return f"{label} {direction} de {previous_value:g} a {current_value:g} {unit}"


def _normalize_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if category(char) != "Mn")
