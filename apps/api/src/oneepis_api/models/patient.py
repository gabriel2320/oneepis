from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin

if TYPE_CHECKING:
    from oneepis_api.models.clinical_record import (
        ActiveProblem,
        Allergy,
        ClinicalAppointment,
        ClinicalEncounter,
        ClinicalEntry,
        ClinicalEvent,
        Medication,
        VitalSign,
    )
    from oneepis_api.models.clinical_risk import ClinicalRisk
    from oneepis_api.models.lab import LabPanel, LabResult


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_class]


class SexAtBirth(enum.StrEnum):
    FEMALE = "female"
    MALE = "male"
    INTERSEX = "intersex"
    UNKNOWN = "unknown"


class PatientClinicalStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CareContext(enum.StrEnum):
    AMBULATORY = "ambulatory"
    HOSPITALIZED = "hospitalized"
    UNKNOWN = "unknown"


class Patient(Base, IdMixin, TimestampMixin):
    __tablename__ = "patients"

    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    preferred_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    birth_date: Mapped[date]
    sex_at_birth: Mapped[SexAtBirth] = mapped_column(
        Enum(SexAtBirth, values_callable=enum_values, name="sex_at_birth"),
        default=SexAtBirth.UNKNOWN,
        nullable=False,
    )
    clinical_status: Mapped[PatientClinicalStatus] = mapped_column(
        Enum(
            PatientClinicalStatus,
            values_callable=enum_values,
            name="patient_clinical_status",
        ),
        default=PatientClinicalStatus.ACTIVE,
        nullable=False,
    )
    current_care_context: Mapped[CareContext] = mapped_column(
        Enum(CareContext, values_callable=enum_values, name="care_context"),
        default=CareContext.UNKNOWN,
        nullable=False,
    )
    document_id_hash: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    clinical_identifier: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    emergency_contact: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    clinical_entries: Mapped[list[ClinicalEntry]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    clinical_events: Mapped[list[ClinicalEvent]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    lab_panels: Mapped[list[LabPanel]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    lab_results: Mapped[list[LabResult]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    allergies: Mapped[list[Allergy]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    medications: Mapped[list[Medication]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    active_problems: Mapped[list[ActiveProblem]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    clinical_risks: Mapped[list[ClinicalRisk]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    encounters: Mapped[list[ClinicalEncounter]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    appointments: Mapped[list[ClinicalAppointment]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    vital_signs: Mapped[list[VitalSign]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
