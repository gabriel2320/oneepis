from __future__ import annotations

from oneepis_api.schemas.clinical_record_contracts.diagnostics import DiagnosticCandidate
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.diagnostic_references import (
    DiagnosticReference,
    diagnostic_references_from_texts,
    normalize_diagnostic_text,
)


def build_diagnostic_candidates(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    lab_results: list[object],
) -> list[DiagnosticCandidate]:
    references = diagnostic_references_from_texts(
        [
            *_event_texts(events),
            *_entry_texts(snapshot.recent_entries),
            *_lab_texts(lab_results),
        ],
        limit=5,
    )
    candidates = [
        _candidate_from_reference(reference, snapshot, events, lab_results)
        for reference in references
        if not _matches_existing_active_problem(reference, snapshot)
    ]
    return [candidate for candidate in candidates if candidate.evidence][:5]


def _candidate_from_reference(
    reference: DiagnosticReference,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    lab_results: list[object],
) -> DiagnosticCandidate:
    evidence = _reference_evidence(reference, snapshot, events, lab_results)
    missing = _candidate_missing_data(reference.domain, snapshot, lab_results)
    certainty = "moderate" if len(evidence) >= 2 and not missing else "low"
    return DiagnosticCandidate(
        candidate_id=reference.reference_id,
        title=reference.title,
        domain=reference.domain,
        certainty=certainty,
        rationale=(
            "Candidato sugerido por coincidencia entre texto clinico estructurado "
            "y referencias diagnosticas locales."
        ),
        evidence=evidence[:5],
        missing_data=missing,
        coding_references=list(reference.coding_references),
        reference_sources=list(reference.reference_sources),
        warnings=[
            reference.clinical_use_limit,
            "Requiere confirmacion humana; OneEpis no diagnostica de forma autonoma.",
            "SNOMED GPS se usa como identificador plano, sin inferencia jerarquica.",
        ],
    )


def _reference_evidence(
    reference: DiagnosticReference,
    snapshot: PatientRecordSnapshot,
    events: list[object],
    lab_results: list[object],
) -> list[str]:
    evidence: list[str] = []
    aliases = _normalized_aliases(reference)
    for event in events[:8]:
        text = normalize_diagnostic_text(str(getattr(event, "summary", "")))
        if _contains_alias(text, aliases):
            evidence.append(f"Evento: {getattr(event, 'summary', 'evento clinico')}")
    for entry in snapshot.recent_entries[:5]:
        sections = [
            getattr(entry, "title", ""),
            getattr(entry, "subjective", ""),
            getattr(entry, "objective", ""),
            getattr(entry, "assessment", ""),
            getattr(entry, "plan", ""),
        ]
        text = normalize_diagnostic_text(" ".join(str(item or "") for item in sections))
        if _contains_alias(text, aliases):
            evidence.append(f"Evolucion: {getattr(entry, 'title', 'evolucion clinica')}")
    for result in lab_results[:8]:
        text = normalize_diagnostic_text(
            " ".join(
                str(getattr(result, attr, "") or "")
                for attr in ("name", "code", "value", "unit")
            )
        )
        if _contains_alias(text, aliases):
            evidence.append(f"Examen: {getattr(result, 'name', 'resultado estructurado')}")
    return _stable_unique(evidence)


def _candidate_missing_data(
    domain: str,
    snapshot: PatientRecordSnapshot,
    lab_results: list[object],
) -> list[str]:
    latest_vitals = snapshot.latest_vitals
    missing: list[str] = []
    if domain == "respiratorio":
        if latest_vitals is None or latest_vitals.oxygen_saturation_pct is None:
            missing.append("Falta saturacion O2 reciente para revisar candidato respiratorio.")
        if latest_vitals is None or latest_vitals.respiratory_rate_bpm is None:
            missing.append("Falta frecuencia respiratoria reciente para revisar candidato.")
    elif domain == "metabolico":
        if not _lab_results_include(("glicemia", "glucosa", "hba1c"), lab_results):
            missing.append("Falta glicemia/HbA1c estructurada para revisar candidato metabolico.")
    elif domain == "hemodinamico":
        if (
            latest_vitals is None
            or latest_vitals.systolic_bp is None
            or latest_vitals.diastolic_bp is None
        ):
            missing.append("Falta presion arterial reciente para revisar candidato.")
    return missing


def _event_texts(events: list[object]) -> list[str]:
    return [str(getattr(event, "summary", "") or "") for event in events[:12]]


def _entry_texts(entries: list[object]) -> list[str]:
    texts: list[str] = []
    for entry in entries[:6]:
        texts.extend(
            str(getattr(entry, field, "") or "")
            for field in ("title", "subjective", "objective", "assessment", "plan")
        )
    return texts


def _lab_texts(lab_results: list[object]) -> list[str]:
    return [
        " ".join(
            str(getattr(result, attr, "") or "")
            for attr in ("name", "code", "value", "unit")
        )
        for result in lab_results[:12]
    ]


def _matches_existing_active_problem(
    reference: DiagnosticReference,
    snapshot: PatientRecordSnapshot,
) -> bool:
    aliases = _normalized_aliases(reference)
    codes = {code.code for code in reference.coding_references}
    for problem in snapshot.active_problems:
        title = normalize_diagnostic_text(problem.title)
        if _contains_alias(title, aliases):
            return True
        if problem.code and problem.code.strip() in codes:
            return True
    return False


def _normalized_aliases(reference: DiagnosticReference) -> set[str]:
    return {
        normalize_diagnostic_text(alias)
        for alias in (reference.title, *reference.aliases)
        if alias.strip()
    }


def _contains_alias(text: str, aliases: set[str]) -> bool:
    return any(alias and alias in text for alias in aliases)


def _lab_results_include(terms: tuple[str, ...], lab_results: list[object]) -> bool:
    normalized_terms = tuple(normalize_diagnostic_text(term) for term in terms)
    return any(
        any(term in text for term in normalized_terms)
        for text in (normalize_diagnostic_text(item) for item in _lab_texts(lab_results))
    )


def _stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
