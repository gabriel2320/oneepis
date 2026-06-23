from __future__ import annotations

import uuid
from unicodedata import category, normalize

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.clinical_record import RecordStatus
from oneepis_api.models.lab import LabPanel, LabResult
from oneepis_api.schemas.clinical_record import ClinicalEvidenceMark, ClinicalIntentSource

_DOMAIN_LAB_TERMS = {
    "metabolico": ("glicemia", "glucosa", "hba1c", "hemoglobina glicosilada"),
    "infeccioso": ("pcr", "proteina c reactiva", "crp", "leucocitos", "procalcitonina"),
    "renal": ("creatinina", "egfr", "filtrado glomerular", "urea", "diuresis"),
}


def fetch_context_lab_results(
    session: Session,
    patient_id: uuid.UUID,
    *,
    limit: int = 20,
) -> list[LabResult]:
    statement = (
        select(LabResult)
        .join(LabPanel)
        .options(selectinload(LabResult.panel))
        .where(
            LabResult.patient_id == patient_id,
            LabResult.status == RecordStatus.ACTIVE,
            LabPanel.status == RecordStatus.ACTIVE,
        )
        .order_by(LabPanel.occurred_at.desc(), LabResult.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def lab_sources(lab_results: list[LabResult]) -> list[ClinicalIntentSource]:
    return [
        ClinicalIntentSource(
            source_type="lab_result",
            source_id=result.id,
            label=lab_result_label(result),
        )
        for result in lab_results[:8]
    ]


def lab_context_items(lab_results: list[LabResult]) -> list[str]:
    return [lab_result_label(result) for result in lab_results[:6]]


def lab_evidence_marks(lab_results: list[LabResult]) -> list[ClinicalEvidenceMark]:
    return [
        ClinicalEvidenceMark(
            label=lab_result_label(result),
            status="confirmed",
            detail="Resultado estructurado activo; fuente inspeccionable en laboratorio.",
            source_id=result.id,
        )
        for result in lab_results[:4]
    ]


def problem_lab_evidence(
    problem: object,
    lab_results: list[LabResult],
) -> list[ClinicalEvidenceMark]:
    domain = _problem_domain(problem)
    terms = _DOMAIN_LAB_TERMS.get(domain or "")
    if not terms:
        return []
    return [
        ClinicalEvidenceMark(
            label=lab_result_label(result),
            status="confirmed",
            detail=f"Resultado estructurado asociado por dominio clinico local: {domain}.",
            source_id=result.id,
        )
        for result in lab_results
        if lab_results_include_terms([result], terms)
    ][:4]


def lab_results_include_terms(lab_results: list[LabResult], terms: tuple[str, ...]) -> bool:
    return any(_contains_any_terms(_lab_text(result), terms) for result in lab_results)


def lab_result_label(result: LabResult) -> str:
    value = result.value
    if value is None and result.numeric_value is not None:
        value = f"{result.numeric_value:g}"
    unit = f" {result.unit}" if result.unit else ""
    flag = f" ({result.flag.value})" if result.flag.value != "unknown" else ""
    return f"{result.name}: {value or 'sin valor'}{unit}{flag}"


def _problem_domain(problem: object) -> str | None:
    text = _normalize_text(str(getattr(problem, "title", "")))
    if any(term in text for term in ("diabetes", "dm2", "glicemia", "glucosa")):
        return "metabolico"
    if any(term in text for term in ("fiebre", "infeccion", "sepsis")):
        return "infeccioso"
    if any(term in text for term in ("renal", "rinon", "nefropatia", "erc")):
        return "renal"
    return None


def _lab_text(result: LabResult) -> str:
    values = [
        result.code,
        result.name,
        result.value,
        result.unit,
        result.reference_range,
        result.notes,
        result.panel.panel_name,
        result.panel.summary,
    ]
    return " ".join(value for value in values if value)


def _contains_any_terms(value: str, terms: tuple[str, ...]) -> bool:
    normalized_value = _normalize_text(value)
    return any(_normalize_text(term) in normalized_value for term in terms)


def _normalize_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if category(char) != "Mn")
