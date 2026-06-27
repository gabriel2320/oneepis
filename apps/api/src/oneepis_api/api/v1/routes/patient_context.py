from __future__ import annotations

import uuid

from fastapi import APIRouter

from oneepis_api.api.deps import PatientReadActorDep
from oneepis_api.schemas.clinical_record import PatientContextResponse
from oneepis_api.services.audit import record_audit_event
from oneepis_api.services.patient_context import build_patient_context

from .patient_shared import PATIENT_ROUTER_OPTIONS, SessionDep, require_patient

router = APIRouter(**PATIENT_ROUTER_OPTIONS)


@router.get("/{patient_id}/context", response_model=PatientContextResponse)
def get_patient_context(
    patient_id: uuid.UUID,
    session: SessionDep,
    actor: PatientReadActorDep,
) -> PatientContextResponse:
    patient = require_patient(session, patient_id)
    context = build_patient_context(session, patient)
    record_audit_event(
        session,
        action="patient_access.context.read",
        entity_type="patient_access",
        entity_id=patient.id,
        actor_id=actor,
    )
    session.commit()
    return context
