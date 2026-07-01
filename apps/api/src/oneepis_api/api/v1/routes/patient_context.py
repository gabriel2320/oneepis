from __future__ import annotations

import uuid

from fastapi import APIRouter

from oneepis_api.api.deps import ReadAccessDep
from oneepis_api.schemas.clinical_record import PatientContextResponse
from oneepis_api.services.patient_context import build_patient_context
from oneepis_api.services.patient_scope_enforcement import enforce_patient_scope_for_read

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    SessionDep,
    SettingsDep,
    record_patient_scoped_read,
    require_patient,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/context", response_model=PatientContextResponse)
def get_patient_context(
    patient_id: uuid.UUID,
    session: SessionDep,
    user: ReadAccessDep,
    settings: SettingsDep,
) -> PatientContextResponse:
    patient = require_patient(session, patient_id)
    enforce_patient_scope_for_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        roles=user.roles,
        settings=settings,
    )
    record_patient_scoped_read(
        session,
        patient_id=patient_id,
        actor_id=user.actor_id,
        action="patient_context.read",
    )
    return build_patient_context(session, patient)
