from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from oneepis_api.models.clinical_record import (
    ClinicalEncounter,
    ClinicalEntry,
    ClinicalEntryKind,
    ClinicalEntryStatus,
    EncounterStatus,
    EncounterType,
    EncounterWorkflowKind,
)
from oneepis_api.schemas.clinical_record import ClinicalEncounterCreate, ClinicalEntryCreate
from oneepis_api.services.audit import audit_snapshot, record_audit_event

ENCOUNTER_UOW_AUDIT_FIELDS = [
    "ended_at",
    "patient_id",
    "started_at",
    "status",
    "type",
    "workflow_kind",
]
ENTRY_UOW_AUDIT_FIELDS = [
    "created_by",
    "encounter_id",
    "kind",
    "occurred_at",
    "patient_id",
    "status",
]


@dataclass(frozen=True)
class CompletedAmbulatoryVisit:
    encounter: ClinicalEncounter
    entry: ClinicalEntry


def complete_ambulatory_visit_with_soap(
    session: Session,
    *,
    patient_id: uuid.UUID,
    actor_id: str,
    encounter: ClinicalEncounterCreate,
    entry: ClinicalEntryCreate,
    before_commit: Callable[[], None] | None = None,
) -> CompletedAmbulatoryVisit:
    """Persist an ambulatory encounter close and SOAP draft as one transaction."""

    _validate_ambulatory_visit(encounter, entry)
    try:
        encounter_model = ClinicalEncounter(patient_id=patient_id, **encounter.model_dump())
        session.add(encounter_model)
        session.flush()
        record_audit_event(
            session,
            action="encounter.created",
            entity_type="encounter",
            entity_id=encounter_model.id,
            actor_id=actor_id,
            metadata={
                "patient_id": str(patient_id),
                "clinical_act_key": "complete_ambulatory_visit",
                "type": encounter_model.type.value,
                "status": encounter_model.status.value,
                "workflow_kind": encounter_model.workflow_kind.value,
            },
            after=audit_snapshot(encounter_model, ENCOUNTER_UOW_AUDIT_FIELDS),
        )

        entry_data = entry.model_dump()
        entry_data["encounter_id"] = encounter_model.id
        entry_data["created_by"] = actor_id
        entry_data["extra_data"] = {
            **entry_data.get("extra_data", {}),
            "clinical_act_key": "complete_ambulatory_visit",
        }
        entry_model = ClinicalEntry(patient_id=patient_id, **entry_data)
        session.add(entry_model)
        session.flush()
        record_audit_event(
            session,
            action="clinical_entry.created",
            entity_type="clinical_entry",
            entity_id=entry_model.id,
            actor_id=actor_id,
            metadata={
                "patient_id": str(patient_id),
                "clinical_act_key": "complete_ambulatory_visit",
                "kind": entry_model.kind.value,
            },
            after=audit_snapshot(entry_model, ENTRY_UOW_AUDIT_FIELDS),
        )
        record_audit_event(
            session,
            action="clinical_act.completed",
            entity_type="patient",
            entity_id=patient_id,
            actor_id=actor_id,
            metadata={
                "patient_id": str(patient_id),
                "clinical_act_key": "complete_ambulatory_visit",
                "encounter_id": str(encounter_model.id),
                "entry_id": str(entry_model.id),
            },
        )
        if before_commit is not None:
            before_commit()
        session.commit()
        session.refresh(encounter_model)
        session.refresh(entry_model)
        return CompletedAmbulatoryVisit(encounter=encounter_model, entry=entry_model)
    except Exception:
        session.rollback()
        raise


def _validate_ambulatory_visit(
    encounter: ClinicalEncounterCreate,
    entry: ClinicalEntryCreate,
) -> None:
    if (
        encounter.type != EncounterType.AMBULATORY
        or encounter.status != EncounterStatus.COMPLETED
        or encounter.workflow_kind != EncounterWorkflowKind.AMBULATORY_VISIT
        or encounter.ended_at is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Ambulatory visit UoW requires a completed ambulatory visit encounter",
        )
    if entry.encounter_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Ambulatory visit UoW owns the entry encounter link",
        )
    if entry.kind != ClinicalEntryKind.PROGRESS or entry.status != ClinicalEntryStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Ambulatory visit UoW creates an unsigned progress SOAP draft",
        )
