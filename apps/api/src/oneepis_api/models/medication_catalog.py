from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.patient import enum_values


class MedicationCatalogStatus(enum.StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DRAFT = "draft"


class MedicationSourceSystem(enum.StrEnum):
    LOCAL_CURATED = "local_curated"
    FDA_OPENFDA_LABEL = "fda_openfda_label"
    FDA_DRUGSFDA = "fda_drugsfda"
    FDA_ENFORCEMENT = "fda_enforcement"
    FDA_FAERS = "fda_faers"
    ISP_ANAMED = "isp_anamed"


class MedicationSourceReviewStatus(enum.StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    DEPRECATED = "deprecated"


class MedicationDoseSeverity(enum.StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MedicationCatalogItem(Base, IdMixin, TimestampMixin):
    __tablename__ = "medication_catalog_items"

    display_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    generic_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    form: Mapped[str | None] = mapped_column(String(80), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(80), nullable=True)
    route: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[MedicationCatalogStatus] = mapped_column(
        Enum(
            MedicationCatalogStatus,
            values_callable=enum_values,
            name="medication_catalog_status",
        ),
        default=MedicationCatalogStatus.AVAILABLE,
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_system: Mapped[MedicationSourceSystem] = mapped_column(
        Enum(
            MedicationSourceSystem,
            values_callable=enum_values,
            name="medication_source_system",
        ),
        default=MedicationSourceSystem.LOCAL_CURATED,
        nullable=False,
    )
    source_label: Mapped[str] = mapped_column(String(160), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    curated_by: Mapped[str] = mapped_column(String(120), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_status: Mapped[MedicationSourceReviewStatus] = mapped_column(
        Enum(
            MedicationSourceReviewStatus,
            values_callable=enum_values,
            name="medication_source_review_status",
        ),
        default=MedicationSourceReviewStatus.DRAFT,
        nullable=False,
    )

    dose_rules: Mapped[list[MedicationDoseRule]] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MedicationDoseRule.created_at",
    )


class MedicationDoseRule(Base, IdMixin, TimestampMixin):
    __tablename__ = "medication_dose_rules"

    catalog_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medication_catalog_items.id", ondelete="CASCADE"),
        index=True,
    )
    population: Mapped[str] = mapped_column(String(80), nullable=False, default="adult_general")
    route: Mapped[str | None] = mapped_column(String(80), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    min_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    max_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    frequency_text: Mapped[str | None] = mapped_column(String(160), nullable=True)
    usual_dose_text: Mapped[str | None] = mapped_column(String(280), nullable=True)
    avoid_dose_text: Mapped[str | None] = mapped_column(String(280), nullable=True)
    severity: Mapped[MedicationDoseSeverity] = mapped_column(
        Enum(
            MedicationDoseSeverity,
            values_callable=enum_values,
            name="medication_dose_severity",
        ),
        default=MedicationDoseSeverity.WARNING,
        nullable=False,
    )
    source_system: Mapped[MedicationSourceSystem] = mapped_column(
        Enum(
            MedicationSourceSystem,
            values_callable=enum_values,
            name="medication_source_system",
        ),
        default=MedicationSourceSystem.LOCAL_CURATED,
        nullable=False,
    )
    source_label: Mapped[str] = mapped_column(String(160), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_status: Mapped[MedicationSourceReviewStatus] = mapped_column(
        Enum(
            MedicationSourceReviewStatus,
            values_callable=enum_values,
            name="medication_source_review_status",
        ),
        default=MedicationSourceReviewStatus.DRAFT,
        nullable=False,
    )

    catalog_item: Mapped[MedicationCatalogItem] = relationship(back_populates="dose_rules")
