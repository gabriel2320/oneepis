from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.appointment import AppointmentStatus as AppointmentStatus
from oneepis_api.models.appointment import ClinicalAppointment as ClinicalAppointment
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.clinical_enums import (
    AllergySeverity,
    ClinicalEntryKind,
    ClinicalEntryStatus,
    ClinicalEventSourceType,
    ClinicalEventType,
    EncounterStatus,
    EncounterType,
    EncounterWorkflowKind,
    RecordStatus,
)
from oneepis_api.models.medication_catalog import MedicationCatalogItem
from oneepis_api.models.patient import enum_values
from oneepis_api.models.vital_sign import VitalSign as VitalSign
from oneepis_api.services.medication_read_support import (
    medication_missing_fields,
    medication_source,
)

if TYPE_CHECKING:
    from oneepis_api.models.patient import Patient


class ClinicalEntry(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_entries"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_encounters.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    kind: Mapped[ClinicalEntryKind] = mapped_column(
        Enum(ClinicalEntryKind, values_callable=enum_values, name="clinical_entry_kind"),
        nullable=False,
    )
    status: Mapped[ClinicalEntryStatus] = mapped_column(
        Enum(ClinicalEntryStatus, values_callable=enum_values, name="clinical_entry_status"),
        default=ClinicalEntryStatus.DRAFT,
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    subjective: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    patient: Mapped[Patient] = relationship(back_populates="clinical_entries")
    encounter: Mapped[ClinicalEncounter | None] = relationship(
        back_populates="clinical_entries",
    )


class ClinicalEvent(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_events"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_encounters.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    event_type: Mapped[ClinicalEventType] = mapped_column(
        Enum(ClinicalEventType, values_callable=enum_values, name="clinical_event_type"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    summary: Mapped[str] = mapped_column(String(280), nullable=False)
    source_type: Mapped[ClinicalEventSourceType] = mapped_column(
        Enum(
            ClinicalEventSourceType,
            values_callable=enum_values,
            name="clinical_event_source_type",
        ),
        default=ClinicalEventSourceType.MANUAL,
        nullable=False,
    )
    source_ref: Mapped[str | None] = mapped_column(String(160), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    patient: Mapped[Patient] = relationship(back_populates="clinical_events")
    encounter: Mapped[ClinicalEncounter | None] = relationship(back_populates="clinical_events")


class Allergy(Base, IdMixin, TimestampMixin):
    __tablename__ = "allergies"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    substance: Mapped[str] = mapped_column(String(160), nullable=False)
    reaction: Mapped[str | None] = mapped_column(String(240), nullable=True)
    severity: Mapped[AllergySeverity] = mapped_column(
        Enum(AllergySeverity, values_callable=enum_values, name="allergy_severity"),
        default=AllergySeverity.UNKNOWN,
        nullable=False,
    )
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, values_callable=enum_values, name="record_status"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="allergies")


class Medication(Base, IdMixin, TimestampMixin):
    __tablename__ = "medications"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    catalog_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medication_catalog_items.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(120), nullable=True)
    route: Mapped[str | None] = mapped_column(String(80), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, values_callable=enum_values, name="record_status"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    started_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    ended_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    dose_check_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    dose_override_reason: Mapped[str | None] = mapped_column(String(280), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="medications")
    catalog_item: Mapped[MedicationCatalogItem | None] = relationship()

    @property
    def source(self) -> dict[str, Any] | None:
        return medication_source(self)

    @property
    def missing_fields(self) -> list[str]:
        return medication_missing_fields(self)


class ActiveProblem(Base, IdMixin, TimestampMixin):
    __tablename__ = "active_problems"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    code_system: Mapped[str | None] = mapped_column(String(80), nullable=True)
    code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, values_callable=enum_values, name="record_status"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolved_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(280), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="active_problems")


class ClinicalEncounter(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_encounters"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    type: Mapped[EncounterType] = mapped_column(
        Enum(EncounterType, values_callable=enum_values, name="encounter_type"),
        default=EncounterType.UNKNOWN,
        nullable=False,
    )
    status: Mapped[EncounterStatus] = mapped_column(
        Enum(EncounterStatus, values_callable=enum_values, name="encounter_status"),
        default=EncounterStatus.IN_PROGRESS,
        nullable=False,
    )
    workflow_kind: Mapped[EncounterWorkflowKind] = mapped_column(
        Enum(
            EncounterWorkflowKind,
            values_callable=enum_values,
            name="encounter_workflow_kind",
        ),
        default=EncounterWorkflowKind.GENERAL,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(320), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="encounters")
    clinical_entries: Mapped[list[ClinicalEntry]] = relationship(
        back_populates="encounter",
        passive_deletes=True,
    )
    clinical_events: Mapped[list[ClinicalEvent]] = relationship(
        back_populates="encounter",
        passive_deletes=True,
    )
