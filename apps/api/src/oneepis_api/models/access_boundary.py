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
    services: Mapped[list[ClinicalService]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )


class ClinicalService(Base, IdMixin, TimestampMixin):
    __tablename__ = "clinical_services"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_clinical_services_tenant_key"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_tenants.id", ondelete="CASCADE"),
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

    tenant: Mapped[ClinicalTenant] = relationship(back_populates="services")
    care_teams: Mapped[list[CareTeam]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",
    )


class CareTeam(Base, IdMixin, TimestampMixin):
    __tablename__ = "care_teams"
    __table_args__ = (UniqueConstraint("service_id", "key", name="uq_care_teams_service_key"),)

    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_services.id", ondelete="CASCADE"),
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

    service: Mapped[ClinicalService] = relationship(back_populates="care_teams")
    patient_relationships: Mapped[list[PatientCareTeamRelationship]] = relationship(
        back_populates="care_team",
        cascade="all, delete-orphan",
    )


class PatientCareTeamRelationship(Base, IdMixin, TimestampMixin):
    __tablename__ = "patient_care_team_relationships"
    __table_args__ = (
        UniqueConstraint("patient_id", "care_team_id", name="uq_patient_care_team_relationship"),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    care_team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("care_teams.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[AccessBoundaryStatus] = mapped_column(
        Enum(
            AccessBoundaryStatus,
            values_callable=enum_values,
            name="access_boundary_status",
        ),
        default=AccessBoundaryStatus.DRAFT,
        nullable=False,
    )
    relationship_reason: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")

    care_team: Mapped[CareTeam] = relationship(back_populates="patient_relationships")
