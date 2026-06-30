from __future__ import annotations

from typing import Any

from oneepis_api.models.clinical_record import ClinicalEvent
from oneepis_api.schemas.clinical_record_contracts.diagnostics import (
    diagnostic_code_references_from_payload,
)
from oneepis_api.schemas.patient import HistoricalDiagnosisRead


def historical_diagnosis_from_event(event: ClinicalEvent) -> HistoricalDiagnosisRead | None:
    antecedent = event.payload.get("antecedent")
    if not isinstance(antecedent, dict) or antecedent.get("category") != "diagnostico_historico":
        return None
    source_label = antecedent.get("source_label")
    limit = antecedent.get("limit")
    if not isinstance(source_label, str) or not isinstance(limit, str):
        return None
    return HistoricalDiagnosisRead(
        source_event_id=event.id,
        title=event.summary,
        occurred_at=event.occurred_at,
        source_type=event.source_type,
        source_ref=event.source_ref,
        source_label=source_label,
        limit=limit,
        code_system=optional_payload_text(event.payload.get("code_system")),
        code=optional_payload_text(event.payload.get("code")),
        coding_references=diagnostic_code_references_from_payload(
            event.payload.get("diagnostic_codes"),
            fallback_label=event.summary,
        ),
    )


def historical_diagnoses_from_events(events: list[ClinicalEvent]) -> list[HistoricalDiagnosisRead]:
    diagnoses = [historical_diagnosis_from_event(event) for event in events]
    return [diagnosis for diagnosis in diagnoses if diagnosis is not None]


def optional_payload_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None
