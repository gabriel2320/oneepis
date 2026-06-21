from __future__ import annotations

import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.patient import enum_values

if TYPE_CHECKING:
    from oneepis_api.models.clinical_record import ClinicalEncounter
    from oneepis_api.models.patient import Patient


class HospitalBedStatus(enum.StrEnum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CLEANING = "cleaning"
    BLOCKED = "blocked"


class HospitalBed(Base, IdMixin, TimestampMixin):
    __tablename__ = "hospital_beds"
    __table_args__ = (
        UniqueConstraint("ward", "room", "bed_label", name="uq_hospital_beds_location"),
    )

    ward: Mapped[str] = mapped_column(String(80), nullable=False)
    room: Mapped[str] = mapped_column(String(80), nullable=False)
    bed_label: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[HospitalBedStatus] = mapped_column(
        Enum(HospitalBedStatus, values_callable=enum_values, name="hospital_bed_status"),
        default=HospitalBedStatus.AVAILABLE,
        nullable=False,
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_encounters.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(240), nullable=True)

    encounter: Mapped[ClinicalEncounter | None] = relationship()


class HospitalDailySheet(Base, IdMixin, TimestampMixin):
    __tablename__ = "hospital_daily_sheets"
    __table_args__ = (
        UniqueConstraint(
            "encounter_id",
            "sheet_date",
            name="uq_hospital_daily_sheets_encounter_date",
        ),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_encounters.id", ondelete="CASCADE"),
        index=True,
    )
    sheet_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    clinical_summary: Mapped[str] = mapped_column(Text, nullable=False)
    overnight_events: Mapped[str | None] = mapped_column(Text, nullable=True)
    active_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    pending_tasks: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    patient: Mapped[Patient] = relationship()
    encounter: Mapped[ClinicalEncounter] = relationship()
