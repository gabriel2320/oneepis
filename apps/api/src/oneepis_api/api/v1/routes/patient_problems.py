from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from oneepis_api.api.deps import ProblemActorDep
from oneepis_api.models.clinical_record import ActiveProblem, RecordStatus
from oneepis_api.schemas.clinical_record import (
    ActiveProblemCreate,
    ActiveProblemRead,
    ActiveProblemUpdate,
)
from oneepis_api.services.audit import audit_snapshot, changed_field_snapshots, record_audit_event

from .patient_shared import (
    PATIENT_ROUTER_OPTIONS,
    LimitQuery,
    OffsetQuery,
    SessionDep,
    apply_update,
    require_patient,
    require_patient_child,
)

router = APIRouter(**PATIENT_ROUTER_OPTIONS)

@router.get("/{patient_id}/problems", response_model=list[ActiveProblemRead])
def list_active_problems(
    patient_id: uuid.UUID,
    session: SessionDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ActiveProblem]:
    require_patient(session, patient_id)
    statement = (
        select(ActiveProblem)
        .where(
            ActiveProblem.patient_id == patient_id,
            ActiveProblem.status == RecordStatus.ACTIVE,
        )
        .order_by(ActiveProblem.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


@router.post(
    "/{patient_id}/problems",
    response_model=ActiveProblemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_active_problem(
    patient_id: uuid.UUID,
    payload: ActiveProblemCreate,
    session: SessionDep,
    actor: ProblemActorDep,
) -> ActiveProblem:
    require_patient(session, patient_id)
    problem = ActiveProblem(patient_id=patient_id, **payload.model_dump())
    session.add(problem)
    session.flush()
    record_audit_event(
        session,
        action="problem.created",
        entity_type="problem",
        entity_id=problem.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "status": problem.status.value},
        after=audit_snapshot(problem),
    )
    session.commit()
    session.refresh(problem)
    return problem


@router.get("/{patient_id}/problems/{problem_id}", response_model=ActiveProblemRead)
def get_active_problem(
    patient_id: uuid.UUID,
    problem_id: uuid.UUID,
    session: SessionDep,
) -> ActiveProblem:
    require_patient(session, patient_id)
    return require_patient_child(
        session,
        ActiveProblem,
        problem_id,
        patient_id,
        "Problem not found",
    )


@router.patch("/{patient_id}/problems/{problem_id}", response_model=ActiveProblemRead)
def update_active_problem(
    patient_id: uuid.UUID,
    problem_id: uuid.UUID,
    payload: ActiveProblemUpdate,
    session: SessionDep,
    actor: ProblemActorDep,
) -> ActiveProblem:
    require_patient(session, patient_id)
    problem = require_patient_child(
        session,
        ActiveProblem,
        problem_id,
        patient_id,
        "Problem not found",
    )
    update_fields = sorted(payload.model_dump(exclude_unset=True).keys())
    before = audit_snapshot(problem, update_fields)
    fields = apply_update(problem, payload)
    before_changed, after_changed = changed_field_snapshots(
        before=before,
        after_model=problem,
        fields=fields,
    )
    record_audit_event(
        session,
        action="problem.updated",
        entity_type="problem",
        entity_id=problem.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id), "fields": fields},
        before=before_changed,
        after=after_changed,
    )
    session.commit()
    session.refresh(problem)
    return problem


@router.delete("/{patient_id}/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_active_problem(
    patient_id: uuid.UUID,
    problem_id: uuid.UUID,
    session: SessionDep,
    actor: ProblemActorDep,
) -> Response:
    require_patient(session, patient_id)
    problem = require_patient_child(
        session,
        ActiveProblem,
        problem_id,
        patient_id,
        "Problem not found",
    )
    before = audit_snapshot(problem, ["status"])
    problem.status = RecordStatus.ENTERED_IN_ERROR
    record_audit_event(
        session,
        action="problem.entered_in_error",
        entity_type="problem",
        entity_id=problem.id,
        actor_id=actor,
        metadata={"patient_id": str(patient_id)},
        before=before,
        after=audit_snapshot(problem, ["status"]),
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
