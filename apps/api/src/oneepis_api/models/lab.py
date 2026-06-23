from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.clinical_record import ClinicalEventSourceType, RecordStatus
from oneepis_api.models.patient import enum_values

if TYPE_CHECKING:
    from oneepis_api.models.clinical_record import ClinicalEncounter
    from oneepis_api.models.patient import Patient


class LabResultFlag(enum.StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    ABNORMAL = "abnormal"
    UNKNOWN = "unknown"


class LabPanel(Base, IdMixin, TimestampMixin):
    __tablename__ = "lab_panels"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_encounters.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    panel_name: Mapped[str] = mapped_column(String(160), nullable=False)
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
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, values_callable=enum_values, name="record_status"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(String(280), nullable=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    patient: Mapped[Patient] = relationship(back_populates="lab_panels")
    encounter: Mapped[ClinicalEncounter | None] = relationship()
    results: Mapped[list[LabResult]] = relationship(
        back_populates="panel",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LabResult.created_at",
    )


class LabResult(Base, IdMixin, TimestampMixin):
    __tablename__ = "lab_results"

    panel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_panels.id", ondelete="CASCADE"),
        index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    value: Mapped[str | None] = mapped_column(String(80), nullable=True)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    flag: Mapped[LabResultFlag] = mapped_column(
        Enum(LabResultFlag, values_callable=enum_values, name="lab_result_flag"),
        default=LabResultFlag.UNKNOWN,
        nullable=False,
    )
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, values_callable=enum_values, name="record_status"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(240), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="lab_results")
    panel: Mapped[LabPanel] = relationship(back_populates="results")
