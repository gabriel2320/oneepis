from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.clinical_record import RecordStatus
from oneepis_api.models.patient import enum_values

if TYPE_CHECKING:
    from oneepis_api.models.clinical_record import ClinicalEncounter
    from oneepis_api.models.patient import Patient


class ClinicalRiskType(enum.StrEnum):
    FALL = "fall"
    PRESSURE_INJURY = "pressure_injury"
    VTE = "vte"
    ISOLATION = "isolation"
    ADVERSE_EVENT = "adverse_event"
    OTHER = "other"


class ClinicalRiskSeverity(enum.StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ClinicalRiskSourceKind(enum.StrEnum):
    MANUAL = "manual"
    VITAL_SIGN = "vital_sign"
    CLINICAL_EVENT = "clinical_event"
    CLINICAL_ENTRY = "clinical_entry"
    LAB_RESULT = "lab_result"


class ClinicalRisk(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_risks"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_encounters.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    risk_type: Mapped[ClinicalRiskType] = mapped_column(
        Enum(ClinicalRiskType, values_callable=enum_values, name="clinical_risk_type"),
        index=True,
        nullable=False,
    )
    severity: Mapped[ClinicalRiskSeverity] = mapped_column(
        Enum(
            ClinicalRiskSeverity,
            values_callable=enum_values,
            name="clinical_risk_severity",
        ),
        default=ClinicalRiskSeverity.UNKNOWN,
        nullable=False,
    )
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, values_callable=enum_values, name="record_status"),
        default=RecordStatus.ACTIVE,
        nullable=False,
    )
    source_kind: Mapped[ClinicalRiskSourceKind] = mapped_column(
        Enum(
            ClinicalRiskSourceKind,
            values_callable=enum_values,
            name="clinical_risk_source_kind",
        ),
        default=ClinicalRiskSourceKind.MANUAL,
        nullable=False,
    )
    source_ref: Mapped[str | None] = mapped_column(String(160), nullable=True)
    reason: Mapped[str] = mapped_column(String(320), nullable=False)
    human_action: Mapped[str | None] = mapped_column(String(320), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    patient: Mapped[Patient] = relationship(back_populates="clinical_risks")
    encounter: Mapped[ClinicalEncounter | None] = relationship()
