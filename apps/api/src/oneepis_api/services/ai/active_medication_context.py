from __future__ import annotations

from typing import Any

from oneepis_api.models.medication_catalog import MedicationSourceReviewStatus
from oneepis_api.schemas.ai import ClinicalAiSuggestion
from oneepis_api.schemas.clinical_record import MedicationRead
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.medication_catalog_farmaco import farmaco_evidence_for_catalog_item_id

READONLY_NOTE = "Lectura contextual solamente; no propone receta, dosis ni orden ejecutable."
FARMACO_CONTEXT_TAGS = {"renal", "hepatica", "embarazo", "lactancia", "interaccion"}


def active_medication_suggestions(
    snapshot: PatientRecordSnapshot,
) -> list[ClinicalAiSuggestion]:
    suggestions: list[ClinicalAiSuggestion] = []
    for medication in snapshot.active_medications[:8]:
        missing = [str(item) for item in medication.missing_fields]
        limitations = _dose_limitations(medication.dose_check_snapshot)
        source_label = medication.source.source_label if medication.source else "Fuente pendiente"
        draft_note = _draft_source_note(medication)
        farmaco_note = _farmaco_txt_note(medication)
        title_state = "requiere curacion" if draft_note else "incompleta" if missing else "con fuente"
        detail_parts = [
            _medication_summary(medication),
            f"Fuente: {source_label}.",
            READONLY_NOTE,
        ]
        if draft_note:
            detail_parts.append(draft_note)
        if farmaco_note:
            detail_parts.append(farmaco_note)
        if missing:
            detail_parts.append(f"Faltantes: {', '.join(missing)}.")
        if limitations:
            detail_parts.append(f"Limites de validacion: {' '.join(limitations[:2])}")
        suggestions.append(
            ClinicalAiSuggestion(
                title=f"Medicacion activa {title_state}: {medication.name}",
                detail=" ".join(detail_parts),
                severity=_medication_context_severity(
                    missing=missing,
                    limitations=limitations,
                    draft_note=draft_note,
                    farmaco_note=farmaco_note,
                    medication=medication,
                ),
                source="local_rules",
                action_label="Revisar fuente Farmaco" if farmaco_note else "Revisar medicacion activa",
            )
        )
    return suggestions[:5]


def medication_context_safety_notes() -> list[str]:
    return [
        "AI-Chart lee medicacion activa como contexto; no prescribe ni valida dosis.",
        "Faltantes y fuentes deben corregirse en la ficha antes de uso clinico.",
    ]


def merge_readonly_suggestions(
    readonly_suggestions: list[ClinicalAiSuggestion],
    model_suggestions: list[ClinicalAiSuggestion],
) -> list[ClinicalAiSuggestion]:
    return _unique_suggestions([*readonly_suggestions, *model_suggestions])[:8]


def _medication_summary(medication: MedicationRead) -> str:
    values = [medication.dose, medication.route, medication.frequency]
    details = " / ".join(value for value in values if value)
    return f"{medication.name}: {details or 'sin dosis/via/frecuencia completa'}."


def _dose_limitations(snapshot: dict[str, Any]) -> list[str]:
    limitations = snapshot.get("limitations")
    if not isinstance(limitations, list):
        return []
    return [str(item) for item in limitations if isinstance(item, str)]


def _draft_source_note(medication: MedicationRead) -> str | None:
    if medication.source is None:
        return None
    if medication.source.review_status != MedicationSourceReviewStatus.DRAFT:
        return None
    return "Ficha de catalogo draft: requiere curacion humana antes de uso clinico."


def _farmaco_txt_note(medication: MedicationRead) -> str | None:
    evidence = farmaco_evidence_for_catalog_item_id(medication.catalog_item_id)
    if not evidence or evidence.get("decision") != "accepted":
        return None
    pages = _short_list(evidence.get("pages"), "paginas")
    tags = _short_list(evidence.get("evidence_tags"), "temas")
    return (
        f"Evidencia TXT Farmaco pendiente de curacion humana ({pages}; {tags}); "
        "no genera uso, alerta ni dosis automatica."
    )


def _medication_context_severity(
    *,
    missing: list[str],
    limitations: list[str],
    draft_note: str | None,
    farmaco_note: str | None,
    medication: MedicationRead,
) -> str:
    if missing or limitations or draft_note:
        return "warning"
    evidence = farmaco_evidence_for_catalog_item_id(medication.catalog_item_id)
    if farmaco_note and evidence:
        if FARMACO_CONTEXT_TAGS.intersection(set(evidence.get("evidence_tags") or [])):
            return "warning"
    return "info"


def _short_list(value: object, label: str) -> str:
    if not isinstance(value, list) or not value:
        return f"{label} sin detalle"
    items = [str(item) for item in value[:4]]
    if len(value) > 4:
        items.append("...")
    return f"{label}: {', '.join(items)}"


def _unique_suggestions(items: list[ClinicalAiSuggestion]) -> list[ClinicalAiSuggestion]:
    seen: set[str] = set()
    output: list[ClinicalAiSuggestion] = []
    for item in items:
        key = f"{item.title}\n{item.detail}".lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output
