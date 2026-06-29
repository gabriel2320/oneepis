from __future__ import annotations

import json

from oneepis_api.schemas.ai import ClinicalAiSuggestion
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.ai.active_medication_context import active_medication_suggestions


def local_snapshot_suggestions(snapshot: PatientRecordSnapshot) -> list[ClinicalAiSuggestion]:
    suggestions: list[ClinicalAiSuggestion] = []
    if snapshot.latest_vitals is None:
        suggestions.append(
            ClinicalAiSuggestion(
                title="Faltan signos vitales recientes",
                detail="No hay un control de signos vitales en el snapshot actual.",
                severity="warning",
                source="local_rules",
                action_label="Registrar signos",
            )
        )

    for entry in snapshot.recent_entries[:3]:
        if not entry.plan:
            suggestions.append(
                ClinicalAiSuggestion(
                    title="Evolucion sin plan explicito",
                    detail=f"La evolucion '{entry.title}' no tiene plan documentado.",
                    severity="warning",
                    source="local_rules",
                    action_label="Revisar SOAP",
                )
            )

    for medication in snapshot.active_medications:
        if medication.started_on is None:
            suggestions.append(
                ClinicalAiSuggestion(
                    title="Medicacion sin fecha de inicio",
                    detail=f"{medication.name} esta activa sin fecha de inicio registrada.",
                    severity="info",
                    source="local_rules",
                    action_label="Revisar medicacion",
                )
            )

    severe_allergies = [
        item.substance for item in snapshot.active_allergies if item.severity == "severe"
    ]
    if severe_allergies:
        suggestions.append(
            ClinicalAiSuggestion(
                title="Alergia severa activa",
                detail=f"Alergias severas registradas: {', '.join(severe_allergies)}.",
                severity="critical",
                source="local_rules",
                action_label="Ver alergias",
            )
        )

    suggestions.extend(active_medication_suggestions(snapshot))

    if not suggestions:
        suggestions.append(
            ClinicalAiSuggestion(
                title="Ficha sin vacios criticos detectados",
                detail="El snapshot no muestra alertas documentales basicas segun reglas locales.",
                severity="info",
                source="local_rules",
            )
        )

    return suggestions[:8]


def snapshot_summary(snapshot: PatientRecordSnapshot) -> str:
    patient = snapshot.patient
    entry_count = len(snapshot.recent_entries)
    allergy_count = len(snapshot.active_allergies)
    medication_count = len(snapshot.active_medications)
    return (
        f"Snapshot de {patient.first_name} {patient.last_name}: "
        f"{entry_count} evoluciones recientes, {allergy_count} alergias activas, "
        f"{medication_count} medicamentos activos."
    )


def snapshot_payload(snapshot: PatientRecordSnapshot) -> str:
    return json.dumps(
        snapshot.model_dump(mode="json"),
        ensure_ascii=True,
        default=str,
    )
