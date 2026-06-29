from __future__ import annotations

from typing import Any

from oneepis_api.schemas.ai import ClinicalAiSuggestion
from oneepis_api.schemas.clinical_record import MedicationRead
from oneepis_api.schemas.patient import PatientRecordSnapshot

READONLY_NOTE = "Lectura contextual solamente; no propone receta, dosis ni orden ejecutable."


def active_medication_suggestions(
    snapshot: PatientRecordSnapshot,
) -> list[ClinicalAiSuggestion]:
    suggestions: list[ClinicalAiSuggestion] = []
    for medication in snapshot.active_medications[:8]:
        missing = [str(item) for item in medication.missing_fields]
        limitations = _dose_limitations(medication.dose_check_snapshot)
        source_label = medication.source.source_label if medication.source else "Fuente pendiente"
        title_state = "incompleta" if missing else "con fuente"
        detail_parts = [
            _medication_summary(medication),
            f"Fuente: {source_label}.",
            READONLY_NOTE,
        ]
        if missing:
            detail_parts.append(f"Faltantes: {', '.join(missing)}.")
        if limitations:
            detail_parts.append(f"Limites de validacion: {' '.join(limitations[:2])}")
        suggestions.append(
            ClinicalAiSuggestion(
                title=f"Medicacion activa {title_state}: {medication.name}",
                detail=" ".join(detail_parts),
                severity="warning" if missing or limitations else "info",
                source="local_rules",
                action_label="Revisar medicacion activa",
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
