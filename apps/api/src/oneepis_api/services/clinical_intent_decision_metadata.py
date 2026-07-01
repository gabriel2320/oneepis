from __future__ import annotations

import uuid

from oneepis_api.schemas.clinical_record import (
    ClinicalIntentActionDecisionRequest,
    ClinicalReviewItemDecisionRequest,
)
from oneepis_api.services.clinical_intent_review import review_item_fingerprint


def text_presence(value: str | None) -> dict[str, int | bool]:
    text = value.strip() if value else ""
    return {"present": bool(text), "length": len(text)}


def clinical_action_decision_metadata(
    patient_id: uuid.UUID,
    payload: ClinicalIntentActionDecisionRequest,
) -> dict[str, object]:
    return {
        "patient_id": str(patient_id),
        "decision": payload.decision,
        "action_type": payload.action_type,
        "action_id": payload.action_id,
        "requires_confirmation": payload.requires_confirmation,
        "label": text_presence(payload.label),
        "description": text_presence(payload.description),
        "note": text_presence(payload.note),
        "applies_changes": False,
    }


def review_item_decision_metadata(
    patient_id: uuid.UUID,
    payload: ClinicalReviewItemDecisionRequest,
) -> dict[str, object]:
    return {
        "patient_id": str(patient_id),
        "decision": payload.decision,
        "item_type": payload.item_type,
        "item_fingerprint": review_item_fingerprint(
            item_type=payload.item_type,
            source_type=payload.source_type,
            source_id=payload.source_id,
            label=payload.label,
        ),
        "source_type": payload.source_type,
        "source_id": str(payload.source_id) if payload.source_id else None,
        "label": text_presence(payload.label),
        "detail": text_presence(payload.detail),
        "note": text_presence(payload.note),
        "applies_changes": False,
    }
