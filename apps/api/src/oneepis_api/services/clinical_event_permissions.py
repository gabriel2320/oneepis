from __future__ import annotations

from fastapi import HTTPException, status

from oneepis_api.models.clinical_record import ClinicalEventType
from oneepis_api.services.auth import AuthenticatedUser, UserRole

CURATED_EVENT_WRITE_ROLES = {UserRole.ADMIN, UserRole.MEDICO, UserRole.DEV}
CURATED_EVENT_TYPES = {
    ClinicalEventType.DIAGNOSIS,
    ClinicalEventType.PROCEDURE,
}
CURATED_ANTECEDENT_CATEGORIES = {
    "diagnostico_historico",
    "procedimiento",
    "plan_longitudinal",
}


def can_write_curated_clinical_event(user: AuthenticatedUser) -> bool:
    return bool(user.roles.intersection(CURATED_EVENT_WRITE_ROLES))


def validate_clinical_event_semantic_write_access(
    *,
    user: AuthenticatedUser,
    current_event_type: ClinicalEventType | None,
    final_event_type: ClinicalEventType,
    payload: dict | None,
) -> None:
    if not requires_curated_clinical_event_role(current_event_type, final_event_type, payload):
        return
    if can_write_curated_clinical_event(user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Curated clinical events require medico/admin/dev role",
    )


def requires_curated_clinical_event_role(
    current_event_type: ClinicalEventType | None,
    final_event_type: ClinicalEventType,
    payload: dict | None,
) -> bool:
    return (
        current_event_type in CURATED_EVENT_TYPES
        or final_event_type in CURATED_EVENT_TYPES
        or has_curated_antecedent_payload(payload)
    )


def has_curated_antecedent_payload(payload: dict | None) -> bool:
    if not isinstance(payload, dict):
        return False
    antecedent = payload.get("antecedent")
    return (
        isinstance(antecedent, dict)
        and antecedent.get("category") in CURATED_ANTECEDENT_CATEGORIES
    )
