from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from oneepis_api.db.base import Base
from oneepis_api.models import AuditEvent, ClinicalEncounter, ClinicalEntry, Patient
from oneepis_api.models.clinical_record import (
    ClinicalEntryKind,
    ClinicalEntryStatus,
    EncounterStatus,
    EncounterType,
    EncounterWorkflowKind,
)
from oneepis_api.models.patient import SexAtBirth
from oneepis_api.schemas.clinical_record import ClinicalEncounterCreate, ClinicalEntryCreate
from oneepis_api.services.clinical_act_unit_of_work import complete_ambulatory_visit_with_soap


@pytest.fixture()
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with testing_session() as session:
        yield session
    Base.metadata.drop_all(engine)


def test_complete_ambulatory_visit_commits_encounter_entry_and_audit(session: Session) -> None:
    patient_id = _create_patient(session)
    result = complete_ambulatory_visit_with_soap(
        session,
        patient_id=patient_id,
        actor_id="medico@oneepis.local",
        encounter=_encounter_payload(),
        entry=_entry_payload(),
    )

    assert result.encounter.patient_id == patient_id
    assert result.encounter.status == EncounterStatus.COMPLETED
    assert result.entry.encounter_id == result.encounter.id
    assert result.entry.created_by == "medico@oneepis.local"
    assert result.entry.extra_data["clinical_act_key"] == "complete_ambulatory_visit"

    actions = [event.action for event in session.scalars(select(AuditEvent)).all()]
    assert actions == [
        "encounter.created",
        "clinical_entry.created",
        "clinical_act.completed",
    ]


def test_complete_ambulatory_visit_rolls_back_all_records_on_late_failure(
    session: Session,
) -> None:
    patient_id = _create_patient(session)

    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        complete_ambulatory_visit_with_soap(
            session,
            patient_id=patient_id,
            actor_id="medico@oneepis.local",
            encounter=_encounter_payload(),
            entry=_entry_payload(),
            before_commit=lambda: (_ for _ in ()).throw(Boom()),
        )

    assert _count(session, ClinicalEncounter) == 0
    assert _count(session, ClinicalEntry) == 0
    assert _count(session, AuditEvent) == 0


def _create_patient(session: Session) -> uuid.UUID:
    patient = Patient(
        first_name="Unidad",
        last_name="Trabajo",
        birth_date=date(1990, 1, 1),
        sex_at_birth=SexAtBirth.UNKNOWN,
    )
    session.add(patient)
    session.commit()
    return patient.id


def _encounter_payload() -> ClinicalEncounterCreate:
    return ClinicalEncounterCreate(
        type=EncounterType.AMBULATORY,
        status=EncounterStatus.COMPLETED,
        workflow_kind=EncounterWorkflowKind.AMBULATORY_VISIT,
        reason="Control ambulatorio",
        started_at=datetime(2026, 6, 24, 9, 0, tzinfo=UTC),
        ended_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
        location_label="Box 1",
    )


def _entry_payload() -> ClinicalEntryCreate:
    return ClinicalEntryCreate(
        kind=ClinicalEntryKind.PROGRESS,
        status=ClinicalEntryStatus.DRAFT,
        occurred_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
        title="Evolucion SOAP ambulatoria",
        subjective="Refiere mejoria.",
        objective="Examen sin hallazgos de alarma.",
        assessment="Control estable.",
        plan="Continuar seguimiento.",
        tags=["soap", "ambulatory"],
    )


def _count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
