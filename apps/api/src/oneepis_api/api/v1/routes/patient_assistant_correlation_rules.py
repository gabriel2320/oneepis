from __future__ import annotations

import uuid

from oneepis_api.models.clinical_record import ClinicalEvent, Medication
from oneepis_api.models.vital_sign import VitalSign
from oneepis_api.schemas.clinical_record import (
    AssistantCorrelationEvidence,
    AssistantCorrelationResult,
)

from .patient_assistant_common import events_matching, medications_matching
from .patient_assistant_correlation_evidence import (
    event_evidence,
    medication_evidence,
    vital_evidence,
)
from .patient_assistant_labs import exam_events_matching, lab_result_evidence


def correlate_preset(
    *,
    preset: str,
    patient_id: uuid.UUID,
    vitals: list[VitalSign],
    events: list[ClinicalEvent],
    lab_results: list[object],
    medications: list[Medication],
) -> AssistantCorrelationResult:
    if preset == "fever_infection":
        return _correlation_result(
            preset=preset,
            label="Fiebre e infeccion",
            evidence=[
                *vital_evidence(
                    patient_id,
                    [
                        vital
                        for vital in vitals
                        if vital.temperature_c is not None and float(vital.temperature_c) >= 38
                    ],
                    label="Fiebre",
                ),
                *lab_result_evidence(
                    patient_id,
                    lab_results,
                    ("pcr", "leucocito", "leucocytes", "crp"),
                    label="Marcador infeccioso estructurado",
                ),
                *event_evidence(
                    patient_id,
                    events_matching(events, "infeccion", "infection", "fiebre", "pcr", "leucocito"),
                    label="Marcador infeccioso textual",
                ),
            ],
            required_labels=("fiebre registrada", "evento o examen compatible"),
        )
    if preset == "renal_medications":
        return _correlation_result(
            preset=preset,
            label="Funcion renal y medicacion",
            evidence=[
                *lab_result_evidence(
                    patient_id,
                    lab_results,
                    ("creatinina", "creatinine", "urea", "egfr"),
                    label="Funcion renal",
                ),
                *event_evidence(
                    patient_id,
                    exam_events_matching(events, ("creatinina", "creatinine", "urea", "egfr")),
                    label="Funcion renal",
                ),
                *medication_evidence(
                    patient_id,
                    medications_matching(
                        medications,
                        "ibuprofeno",
                        "ketorolaco",
                        "enalapril",
                        "losartan",
                        "furosemida",
                        "metformina",
                        "vancomicina",
                    ),
                    label="Medicacion con revision renal",
                ),
            ],
            required_labels=("examen renal numerico o textual", "medicacion relevante activa"),
        )
    if preset == "respiratory_oxygen":
        return _correlation_result(
            preset=preset,
            label="Respiratorio y oxigenacion",
            evidence=[
                *vital_evidence(
                    patient_id,
                    [
                        vital
                        for vital in vitals
                        if (
                            vital.oxygen_saturation_pct is not None
                            and float(vital.oxygen_saturation_pct) < 92
                        )
                        or (
                            vital.respiratory_rate_bpm is not None
                            and vital.respiratory_rate_bpm > 24
                        )
                    ],
                    label="Oxigenacion o frecuencia respiratoria",
                ),
                *event_evidence(
                    patient_id,
                    events_matching(events, "disnea", "neumonia", "oxigeno", "hipox", "tos"),
                    label="Evento respiratorio textual",
                ),
            ],
            required_labels=("signo vital respiratorio alterado", "evento respiratorio textual"),
        )
    if preset == "hemoglobin_bleeding":
        return _correlation_result(
            preset=preset,
            label="Hemoglobina y sangrado",
            evidence=[
                *lab_result_evidence(
                    patient_id,
                    lab_results,
                    ("hemoglobina", "hemoglobin", "hb", "hto"),
                    label="Serie roja",
                ),
                *event_evidence(
                    patient_id,
                    exam_events_matching(events, ("hemoglobina", "hemoglobin", "hb", "hto")),
                    label="Serie roja",
                ),
                *event_evidence(
                    patient_id,
                    events_matching(events, "sangrado", "hemorrag", "melena", "hematemesis"),
                    label="Evento de sangrado textual",
                ),
            ],
            required_labels=("examen de hemoglobina", "evento de sangrado textual"),
        )
    return _correlation_result(
        preset="medication_changes",
        label="Cambios de medicacion",
        evidence=[
            *event_evidence(
                patient_id,
                events_matching(
                    events,
                    "inicia",
                    "inicio",
                    "suspende",
                    "suspension",
                    "ajuste",
                    "cambio",
                    "aumenta",
                    "disminuye",
                    "medicacion",
                ),
                label="Cambio de medicacion textual",
            ),
            *medication_evidence(patient_id, medications, label="Medicacion activa"),
        ],
        required_labels=("evento de cambio de medicacion", "medicacion activa"),
    )


def correlation_missing_data(
    *,
    vitals: list[VitalSign],
    events: list[ClinicalEvent],
    lab_results: list[object],
    medications: list[Medication],
) -> list[str]:
    missing = []
    if not vitals:
        missing.append("No hay signos vitales estructurados para correlacionar.")
    if not events and not lab_results:
        missing.append("No hay eventos clinicos ni examenes estructurados para correlacionar.")
    if not medications:
        missing.append("No hay medicacion activa estructurada para correlacionar.")
    return missing


def correlation_warnings(*, has_more: bool, limit: int) -> list[str]:
    if not has_more:
        return []
    return [f"Correlacion limitada a {limit} registros por dominio."]


def _correlation_result(
    *,
    preset: str,
    label: str,
    evidence: list[AssistantCorrelationEvidence],
    required_labels: tuple[str, str],
) -> AssistantCorrelationResult:
    found_labels = {item.label for item in evidence}
    missing_data = []
    if len(found_labels) < 2:
        missing_data = [
            "Falta evidencia para correlacion completa: "
            f"{required_labels[0]} y {required_labels[1]}."
        ]
    summary = (
        "Relacion temporal descriptiva con evidencia fuente; requiere interpretacion humana."
        if not missing_data
        else "Evidencia insuficiente para correlacion descriptiva completa."
    )
    evidence.sort(key=lambda item: item.occurred_at, reverse=True)
    return AssistantCorrelationResult(
        preset=preset,
        label=label,
        summary=summary,
        evidence=evidence,
        missing_data=missing_data,
    )
