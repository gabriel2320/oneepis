from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.patient import enum_values

if TYPE_CHECKING:
    from oneepis_api.models.clinical_record import ClinicalEncounter
    from oneepis_api.models.patient import Patient


class ClinicalOrderStatus(enum.StrEnum):
    DRAFT = "draft"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered_in_error"


class ClinicalOrderKind(enum.StrEnum):
    LAB = "lab"
    IMAGING = "imaging"
    NURSING = "nursing"
    OTHER = "other"


class ClinicalOrder(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_orders"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_encounters.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[ClinicalOrderStatus] = mapped_column(
        Enum(
            ClinicalOrderStatus,
            values_callable=enum_values,
            name="clinical_order_status",
        ),
        default=ClinicalOrderStatus.DRAFT,
        nullable=False,
    )
    kind: Mapped[ClinicalOrderKind] = mapped_column(
        Enum(
            ClinicalOrderKind,
            values_callable=enum_values,
            name="clinical_order_kind",
        ),
        default=ClinicalOrderKind.OTHER,
        nullable=False,
    )
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    order_text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    patient: Mapped[Patient] = relationship()
    encounter: Mapped[ClinicalEncounter] = relationship()
