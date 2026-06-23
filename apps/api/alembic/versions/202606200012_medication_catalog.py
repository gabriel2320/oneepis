"""medication catalog and dose checks

Revision ID: 202606200012
Revises: 202606200011
Create Date: 2026-06-23
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "202606200012"
down_revision = "202606200011"
branch_labels = None
depends_on = None


catalog_status = postgresql.ENUM(
    "available",
    "unavailable",
    "draft",
    name="medication_catalog_status",
    create_type=False,
)
source_system = postgresql.ENUM(
    "local_curated",
    "fda_openfda_label",
    "fda_drugsfda",
    "fda_enforcement",
    "fda_faers",
    "isp_anamed",
    name="medication_source_system",
    create_type=False,
)
review_status = postgresql.ENUM(
    "draft",
    "reviewed",
    "deprecated",
    name="medication_source_review_status",
    create_type=False,
)
dose_severity = postgresql.ENUM(
    "info",
    "warning",
    "critical",
    name="medication_dose_severity",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    catalog_status.create(bind, checkfirst=True)
    source_system.create(bind, checkfirst=True)
    review_status.create(bind, checkfirst=True)
    dose_severity.create(bind, checkfirst=True)

    op.create_table(
        "medication_catalog_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("generic_name", sa.String(length=160), nullable=False),
        sa.Column("form", sa.String(length=80), nullable=True),
        sa.Column("strength", sa.String(length=80), nullable=True),
        sa.Column("route", sa.String(length=80), nullable=True),
        sa.Column("status", catalog_status, nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_system", source_system, nullable=False),
        sa.Column("source_label", sa.String(length=160), nullable=False),
        sa.Column("source_url", sa.String(length=400), nullable=True),
        sa.Column("external_id", sa.String(length=120), nullable=True),
        sa.Column("source_version", sa.String(length=80), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("curated_by", sa.String(length=120), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_status", review_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_medication_catalog_items_display_name"),
        "medication_catalog_items",
        ["display_name"],
    )
    op.create_index(
        op.f("ix_medication_catalog_items_generic_name"),
        "medication_catalog_items",
        ["generic_name"],
    )

    op.create_table(
        "medication_dose_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("catalog_item_id", sa.Uuid(), nullable=False),
        sa.Column("population", sa.String(length=80), nullable=False),
        sa.Column("route", sa.String(length=80), nullable=True),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("min_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("max_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("frequency_text", sa.String(length=160), nullable=True),
        sa.Column("usual_dose_text", sa.String(length=280), nullable=True),
        sa.Column("avoid_dose_text", sa.String(length=280), nullable=True),
        sa.Column("severity", dose_severity, nullable=False),
        sa.Column("source_system", source_system, nullable=False),
        sa.Column("source_label", sa.String(length=160), nullable=False),
        sa.Column("source_url", sa.String(length=400), nullable=True),
        sa.Column("external_id", sa.String(length=120), nullable=True),
        sa.Column("source_version", sa.String(length=80), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_status", review_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["catalog_item_id"],
            ["medication_catalog_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_medication_dose_rules_catalog_item_id"),
        "medication_dose_rules",
        ["catalog_item_id"],
    )

    _seed_demo_catalog()

    op.add_column("medications", sa.Column("catalog_item_id", sa.Uuid(), nullable=True))
    op.add_column(
        "medications",
        sa.Column(
            "dose_check_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "medications",
        sa.Column("dose_override_reason", sa.String(length=280), nullable=True),
    )
    op.create_index(op.f("ix_medications_catalog_item_id"), "medications", ["catalog_item_id"])
    op.create_foreign_key(
        "fk_medications_catalog_item_id",
        "medications",
        "medication_catalog_items",
        ["catalog_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("medications", "dose_check_snapshot", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_medications_catalog_item_id", "medications", type_="foreignkey")
    op.drop_index(op.f("ix_medications_catalog_item_id"), table_name="medications")
    op.drop_column("medications", "dose_override_reason")
    op.drop_column("medications", "dose_check_snapshot")
    op.drop_column("medications", "catalog_item_id")

    op.drop_index(
        op.f("ix_medication_dose_rules_catalog_item_id"),
        table_name="medication_dose_rules",
    )
    op.drop_table("medication_dose_rules")
    op.drop_index(
        op.f("ix_medication_catalog_items_generic_name"),
        table_name="medication_catalog_items",
    )
    op.drop_index(
        op.f("ix_medication_catalog_items_display_name"),
        table_name="medication_catalog_items",
    )
    op.drop_table("medication_catalog_items")

    bind = op.get_bind()
    dose_severity.drop(bind, checkfirst=True)
    review_status.drop(bind, checkfirst=True)
    source_system.drop(bind, checkfirst=True)
    catalog_status.drop(bind, checkfirst=True)


def _seed_demo_catalog() -> None:
    source_label = "Fixture demo OneEpis; no uso clinico"
    catalog = sa.table(
        "medication_catalog_items",
        sa.column("id", sa.Uuid()),
        sa.column("display_name", sa.String()),
        sa.column("generic_name", sa.String()),
        sa.column("form", sa.String()),
        sa.column("strength", sa.String()),
        sa.column("route", sa.String()),
        sa.column("status", sa.String()),
        sa.column("tags", postgresql.JSONB(astext_type=sa.Text())),
        sa.column("source_system", sa.String()),
        sa.column("source_label", sa.String()),
        sa.column("curated_by", sa.String()),
        sa.column("review_status", sa.String()),
    )
    rules = sa.table(
        "medication_dose_rules",
        sa.column("id", sa.Uuid()),
        sa.column("catalog_item_id", sa.Uuid()),
        sa.column("population", sa.String()),
        sa.column("route", sa.String()),
        sa.column("unit", sa.String()),
        sa.column("min_value", sa.Numeric()),
        sa.column("max_value", sa.Numeric()),
        sa.column("frequency_text", sa.String()),
        sa.column("usual_dose_text", sa.String()),
        sa.column("avoid_dose_text", sa.String()),
        sa.column("severity", sa.String()),
        sa.column("source_system", sa.String()),
        sa.column("source_label", sa.String()),
        sa.column("review_status", sa.String()),
    )
    op.bulk_insert(
        catalog,
        [
            {
                "id": uuid.UUID("10000000-0000-4000-8000-000000000101"),
                "display_name": "Analgesico demo 500 mg comprimido",
                "generic_name": "analgesico-demo",
                "form": "comprimido",
                "strength": "500 mg",
                "route": "oral",
                "status": "available",
                "tags": ["dolor", "fiebre", "demo"],
                "source_system": "local_curated",
                "source_label": source_label,
                "curated_by": "oneepis.demo",
                "review_status": "reviewed",
            },
            {
                "id": uuid.UUID("10000000-0000-4000-8000-000000000102"),
                "display_name": "Cardio demo 10 mg comprimido",
                "generic_name": "cardio-demo",
                "form": "comprimido",
                "strength": "10 mg",
                "route": "oral",
                "status": "available",
                "tags": ["presion", "cardio", "demo"],
                "source_system": "local_curated",
                "source_label": source_label,
                "curated_by": "oneepis.demo",
                "review_status": "reviewed",
            },
        ],
    )
    op.bulk_insert(
        rules,
        [
            {
                "id": uuid.UUID("10000000-0000-4000-8000-000000000201"),
                "catalog_item_id": uuid.UUID("10000000-0000-4000-8000-000000000101"),
                "population": "adult_general_demo",
                "route": "oral",
                "unit": "mg",
                "min_value": 100,
                "max_value": 1000,
                "frequency_text": "cada 6-8 horas",
                "usual_dose_text": "Rango demo: 100-1000 mg por dosis.",
                "avoid_dose_text": "Evitar dosis demo sobre 1000 mg por toma sin justificacion.",
                "severity": "warning",
                "source_system": "local_curated",
                "source_label": source_label,
                "review_status": "reviewed",
            },
            {
                "id": uuid.UUID("10000000-0000-4000-8000-000000000202"),
                "catalog_item_id": uuid.UUID("10000000-0000-4000-8000-000000000102"),
                "population": "adult_general_demo",
                "route": "oral",
                "unit": "mg",
                "min_value": 5,
                "max_value": 20,
                "frequency_text": "cada 24 horas",
                "usual_dose_text": "Rango demo: 5-20 mg por dosis.",
                "avoid_dose_text": "Evitar dosis demo sobre 20 mg sin justificacion.",
                "severity": "critical",
                "source_system": "local_curated",
                "source_label": source_label,
                "review_status": "reviewed",
            },
        ],
    )
