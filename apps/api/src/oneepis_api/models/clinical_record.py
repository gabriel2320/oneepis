from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.patient import enum_values

if TYPE_CHECKING:
    from oneepis_api.models.patient import Patient


class ClinicalEntryKind(enum.StrEnum):
    INTAKE = "intake"
    PROGRESS = "progress"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    PROCEDURE = "procedure"
    NOTE = "note"


class ClinicalEntryStatus(enum.StrEnum):
    DRAFT = "draft"
    SIGNED = "signed"
    AMENDED = "amended"


class AllergySeverity(enum.StrEnum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class RecordStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    ENTERED_IN_ERROR = "entered_in_error"


class EncounterType(enum.StrEnum):
    AMBULATORY = "ambulatory"
    HOSPITALIZATION = "hospitalization"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


class EncounterStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


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

    patient: Mapped[Patient] = relationship(back_populates="medications")


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


class VitalSign(Base, IdMixin, TimestampMixin):
    __tablename__ = "vital_signs"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heart_rate_bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respiratory_rate_bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    oxygen_saturation_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(240), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="vital_signs")
