from __future__ import annotations

from fastapi import HTTPException, status

from oneepis_api.models.clinical_record import ClinicalEventType
from oneepis_api.services.auth import AuthenticatedUser, UserRole

DIAGNOSIS_EVENT_WRITE_ROLES = {UserRole.ADMIN, UserRole.MEDICO, UserRole.DEV}


def can_write_diagnosis_event(user: AuthenticatedUser) -> bool:
    return bool(user.roles.intersection(DIAGNOSIS_EVENT_WRITE_ROLES))


def validate_diagnosis_event_write_access(
    *,
    user: AuthenticatedUser,
    current_event_type: ClinicalEventType | None,
    final_event_type: ClinicalEventType,
    payload: dict | None,
) -> None:
    if not requires_diagnosis_event_role(current_event_type, final_event_type, payload):
        return
    if can_write_diagnosis_event(user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Diagnosis events require medico/admin/dev role",
    )


def requires_diagnosis_event_role(
    current_event_type: ClinicalEventType | None,
    final_event_type: ClinicalEventType,
    payload: dict | None,
) -> bool:
    return (
        current_event_type == ClinicalEventType.DIAGNOSIS
        or final_event_type == ClinicalEventType.DIAGNOSIS
        or is_historical_diagnosis_payload(payload)
    )


def is_historical_diagnosis_payload(payload: dict | None) -> bool:
    if not isinstance(payload, dict):
        return False
    antecedent = payload.get("antecedent")
    return (
        isinstance(antecedent, dict)
        and antecedent.get("category") == "diagnostico_historico"
    )
