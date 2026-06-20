from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.patient import enum_values

if TYPE_CHECKING:
    from oneepis_api.models.clinical_record import ClinicalEncounter


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
