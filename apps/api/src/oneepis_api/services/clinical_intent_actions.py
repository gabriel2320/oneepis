from __future__ import annotations

from oneepis_api.schemas.clinical_record import ClinicalIntentAction
from oneepis_api.services.clinical_intent_text import normalize_text as _normalize_text


def clinical_intent_action(
    action_type: str,
    label: str,
    description: str,
    *,
    requires_confirmation: bool = False,
) -> ClinicalIntentAction:
    return ClinicalIntentAction(
        action_type=action_type,
        action_id=f"{action_type}:{_normalize_text(label).replace(' ', '_')}",
        label=label,
        description=description,
        confirmation_label="Revisar y confirmar" if requires_confirmation else "Revisar",
        requires_confirmation=requires_confirmation,
    )
