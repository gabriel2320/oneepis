from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oneepis_api.db.base import Base
from oneepis_api.models.base import IdMixin, TimestampMixin
from oneepis_api.models.patient import enum_values


class AccessBoundaryStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class ClinicalInstitution(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_institutions"
    __table_args__ = (UniqueConstraint("key", name="uq_clinical_institutions_key"),)

    key: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[AccessBoundaryStatus] = mapped_column(
        Enum(
            AccessBoundaryStatus,
            values_callable=enum_values,
            name="access_boundary_status",
        ),
        default=AccessBoundaryStatus.DRAFT,
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    tenants: Mapped[list[ClinicalTenant]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )


class ClinicalTenant(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_tenants"
    __table_args__ = (
        UniqueConstraint("institution_id", "key", name="uq_clinical_tenants_institution_key"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_institutions.id", ondelete="CASCADE"),
        index=True,
    )
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[AccessBoundaryStatus] = mapped_column(
        Enum(
            AccessBoundaryStatus,
            values_callable=enum_values,
            name="access_boundary_status",
        ),
        default=AccessBoundaryStatus.DRAFT,
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    institution: Mapped[ClinicalInstitution] = relationship(back_populates="tenants")
