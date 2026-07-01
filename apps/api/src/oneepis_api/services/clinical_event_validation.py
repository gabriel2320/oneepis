from __future__ import annotations

from fastapi import HTTPException, status
from pydantic import ValidationError

from oneepis_api.models.clinical_record import ClinicalEventSourceType, ClinicalEventType
from oneepis_api.schemas.clinical_record_contracts.diagnostics import (
    diagnostic_code_references_from_payload,
    validate_diagnosis_code_pair,
)

CURATED_ANTECEDENT_CATEGORIES = {
    "diagnostico_historico",
    "procedimiento",
    "familiar_social",
    "plan_longitudinal",
}
CURATED_ANTECEDENT_EVENT_TYPES = {
    "diagnostico_historico": ClinicalEventType.DIAGNOSIS,
    "procedimiento": ClinicalEventType.PROCEDURE,
    "familiar_social": ClinicalEventType.CLINICAL_NOTE,
    "plan_longitudinal": ClinicalEventType.CARE_PLAN,
}
CLINICAL_EVENT_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "event_type",
    "occurred_at",
    "patient_id",
    "source_ref",
    "source_type",
]


def validate_clinical_event_source(
    source_type: ClinicalEventSourceType,
    source_ref: str | None,
) -> None:
    if source_type == ClinicalEventSourceType.MANUAL or source_ref:
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="source_ref is required when source_type is not manual",
    )


def validate_curated_antecedent_payload(
    payload: dict,
    event_type: ClinicalEventType,
) -> None:
    if "antecedent" not in payload:
        return
    antecedent = payload["antecedent"]
    if not isinstance(antecedent, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="payload.antecedent must be an object",
        )

    category = antecedent.get("category")
    source_label = antecedent.get("source_label")
    limit = antecedent.get("limit")
    required_values = (category, source_label, limit)
    if not all(isinstance(value, str) and value.strip() for value in required_values):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="payload.antecedent requires category, source_label and limit",
        )
    if category not in CURATED_ANTECEDENT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="payload.antecedent.category is not allowed",
        )
    expected_event_type = CURATED_ANTECEDENT_EVENT_TYPES[category]
    if event_type != expected_event_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "payload.antecedent.category requires event_type "
                f"{expected_event_type.value}"
            ),
        )


def validate_diagnostic_coding_payload(payload: dict, summary: str = "Diagnostico") -> None:
    try:
        validate_diagnosis_code_pair(
            payload.get("code_system") if isinstance(payload.get("code_system"), str) else None,
            payload.get("code") if isinstance(payload.get("code"), str) else None,
        )
        if "diagnostic_codes" not in payload:
            return
        if not isinstance(payload["diagnostic_codes"], list):
            raise ValueError("payload.diagnostic_codes must be a list")
        diagnostic_code_references_from_payload(
            payload["diagnostic_codes"],
            fallback_label=summary,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


def clinical_event_audit_fields(fields: list[str]) -> list[str]:
    allowed_fields = set(CLINICAL_EVENT_AUDIT_FIELDS)
    return [field for field in fields if field in allowed_fields]
