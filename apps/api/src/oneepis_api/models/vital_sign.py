from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.clinical_record import RecordStatus, enum_values

if TYPE_CHECKING:
    from oneepis_api.models.patient import Patient


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
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, values_callable=enum_values, name="record_status"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(240), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="vital_signs")
