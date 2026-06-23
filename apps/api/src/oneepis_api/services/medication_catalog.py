from __future__ import annotations

import re
import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.clinical_record import (
    Medication,
    RecordStatus,
)
from oneepis_api.models.medication_catalog import (
    MedicationCatalogItem,
    MedicationCatalogStatus,
    MedicationDoseRule,
    MedicationDoseSeverity,
    MedicationSourceReviewStatus,
    MedicationSourceSystem,
)
from oneepis_api.schemas.clinical_record import (
    MedicationDoseWarning,
    MedicationDraftValidationRequest,
    MedicationDraftValidationResponse,
    MedicationSourceReference,
)

DEMO_ANALGESIC_ID = uuid.UUID("10000000-0000-4000-8000-000000000101")
DEMO_ANALGESIC_RULE_ID = uuid.UUID("10000000-0000-4000-8000-000000000201")
DEMO_CARDIO_ID = uuid.UUID("10000000-0000-4000-8000-000000000102")
DEMO_CARDIO_RULE_ID = uuid.UUID("10000000-0000-4000-8000-000000000202")
DEMO_SOURCE_LABEL = "Fixture demo OneEpis; no uso clinico"


def ensure_demo_medication_catalog(session: Session) -> None:
    if session.get(MedicationCatalogItem, DEMO_ANALGESIC_ID) is not None:
        return

    analgesic = MedicationCatalogItem(
        id=DEMO_ANALGESIC_ID,
        display_name="Analgesico demo 500 mg comprimido",
        generic_name="analgesico-demo",
        form="comprimido",
        strength="500 mg",
        route="oral",
        status=MedicationCatalogStatus.AVAILABLE,
        tags=["dolor", "fiebre", "demo"],
        source_system=MedicationSourceSystem.LOCAL_CURATED,
        source_label=DEMO_SOURCE_LABEL,
        curated_by="oneepis.demo",
        review_status=MedicationSourceReviewStatus.REVIEWED,
    )
    analgesic.dose_rules = [
        MedicationDoseRule(
            id=DEMO_ANALGESIC_RULE_ID,
            population="adult_general_demo",
            route="oral",
            unit="mg",
            min_value=Decimal("100"),
            max_value=Decimal("1000"),
            frequency_text="cada 6-8 horas",
            usual_dose_text="Rango demo: 100-1000 mg por dosis.",
            avoid_dose_text="Evitar dosis demo sobre 1000 mg por toma sin justificacion.",
            severity=MedicationDoseSeverity.WARNING,
            source_system=MedicationSourceSystem.LOCAL_CURATED,
            source_label=DEMO_SOURCE_LABEL,
            review_status=MedicationSourceReviewStatus.REVIEWED,
        )
    ]
    cardio = MedicationCatalogItem(
        id=DEMO_CARDIO_ID,
        display_name="Cardio demo 10 mg comprimido",
        generic_name="cardio-demo",
        form="comprimido",
        strength="10 mg",
        route="oral",
        status=MedicationCatalogStatus.AVAILABLE,
        tags=["presion", "cardio", "demo"],
        source_system=MedicationSourceSystem.LOCAL_CURATED,
        source_label=DEMO_SOURCE_LABEL,
        curated_by="oneepis.demo",
        review_status=MedicationSourceReviewStatus.REVIEWED,
    )
    cardio.dose_rules = [
        MedicationDoseRule(
            id=DEMO_CARDIO_RULE_ID,
            population="adult_general_demo",
            route="oral",
            unit="mg",
            min_value=Decimal("5"),
            max_value=Decimal("20"),
            frequency_text="cada 24 horas",
            usual_dose_text="Rango demo: 5-20 mg por dosis.",
            avoid_dose_text="Evitar dosis demo sobre 20 mg sin justificacion.",
            severity=MedicationDoseSeverity.CRITICAL,
            source_system=MedicationSourceSystem.LOCAL_CURATED,
            source_label=DEMO_SOURCE_LABEL,
            review_status=MedicationSourceReviewStatus.REVIEWED,
        )
    ]
    session.add_all([analgesic, cardio])
    session.flush()


def list_catalog_items(
    session: Session,
    *,
    query: str | None,
    limit: int,
) -> list[MedicationCatalogItem]:
    ensure_demo_medication_catalog(session)
    statement = (
        select(MedicationCatalogItem)
        .options(selectinload(MedicationCatalogItem.dose_rules))
        .where(MedicationCatalogItem.status == MedicationCatalogStatus.AVAILABLE)
        .order_by(MedicationCatalogItem.display_name.asc())
        .limit(limit)
    )
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                MedicationCatalogItem.display_name.ilike(pattern),
                MedicationCatalogItem.generic_name.ilike(pattern),
            )
        )
    return list(session.scalars(statement))


def get_catalog_item(session: Session, item_id: uuid.UUID) -> MedicationCatalogItem | None:
    ensure_demo_medication_catalog(session)
    statement = (
        select(MedicationCatalogItem)
        .options(selectinload(MedicationCatalogItem.dose_rules))
        .where(MedicationCatalogItem.id == item_id)
    )
    return session.scalar(statement)


def validate_medication_draft(
    session: Session,
    payload: MedicationDraftValidationRequest,
) -> MedicationDraftValidationResponse:
    item = _find_catalog_item(session, payload)
    response = MedicationDraftValidationResponse(
        limitations=[
            "Validacion no ejecutable: no reemplaza juicio clinico ni literatura local revisada.",
            "Pediatria, embarazo, renal/hepatica e interacciones requieren regla explicita.",
        ],
    )
    if item is None:
        response.limitations.append("Sin medicamento de catalogo: no hay regla segura disponible.")
        return response

    reviewed_rules = [
        rule
        for rule in item.dose_rules
        if rule.review_status == MedicationSourceReviewStatus.REVIEWED
        and _route_matches(rule.route, payload.route or item.route)
    ]
    response.source_refs.append(_source_from_item(item))
    if not reviewed_rules:
        response.limitations.append("Sin regla revisada aplicable para esta via.")
        return response

    dose_value = _parse_first_decimal(payload.dose)
    response.normalized_dose = {
        "value": str(dose_value) if dose_value is not None else None,
        "raw": payload.dose,
    }
    if dose_value is None:
        response.limitations.append("Sin dosis numerica interpretable para validar rango.")
        return response

    for rule in reviewed_rules:
        response.source_refs.append(_source_from_rule(rule))
        if rule.unit and payload.dose and rule.unit.lower() not in payload.dose.lower():
            response.limitations.append(f"Unidad esperada no confirmada: {rule.unit}.")
        outside_min = rule.min_value is not None and dose_value < rule.min_value
        outside_max = rule.max_value is not None and dose_value > rule.max_value
        if outside_min or outside_max:
            response.blocking = True
            response.warnings.append(
                MedicationDoseWarning(
                    severity=rule.severity,
                    message=_dose_warning_message(rule, dose_value),
                    requires_override=True,
                    rule_id=rule.id,
                    source=_source_from_rule(rule),
                )
            )
    return response


def medication_dose_snapshot(
    session: Session,
    payload: MedicationDraftValidationRequest,
) -> dict:
    validation = validate_medication_draft(session, payload)
    return validation.model_dump(mode="json")


def patient_medication_suggestions(
    catalog_items: list[MedicationCatalogItem],
    recent_medications: list[Medication],
) -> list[MedicationCatalogItem]:
    recent_terms = {
        medication.name.lower()
        for medication in recent_medications
        if medication.status == RecordStatus.ACTIVE
    }
    suggestions = [
        item
        for item in catalog_items
        if any(
            term in item.display_name.lower() or term in item.generic_name.lower()
            for term in recent_terms
        )
    ]
    return suggestions[:5] or catalog_items[:3]


def _find_catalog_item(
    session: Session,
    payload: MedicationDraftValidationRequest,
) -> MedicationCatalogItem | None:
    if payload.catalog_item_id:
        return get_catalog_item(session, payload.catalog_item_id)
    ensure_demo_medication_catalog(session)
    normalized = payload.name.strip().lower()
    if not normalized:
        return None
    statement = (
        select(MedicationCatalogItem)
        .options(selectinload(MedicationCatalogItem.dose_rules))
        .where(
            or_(
                MedicationCatalogItem.display_name.ilike(f"%{normalized}%"),
                MedicationCatalogItem.generic_name.ilike(f"%{normalized}%"),
            )
        )
        .order_by(MedicationCatalogItem.display_name.asc())
        .limit(1)
    )
    return session.scalar(statement)


def _parse_first_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    match = re.search(r"\d+(?:[.,]\d+)?", value)
    if not match:
        return None
    try:
        return Decimal(match.group(0).replace(",", "."))
    except InvalidOperation:
        return None


def _route_matches(rule_route: str | None, draft_route: str | None) -> bool:
    if not rule_route or not draft_route:
        return True
    return rule_route.strip().lower() == draft_route.strip().lower()


def _source_from_item(item: MedicationCatalogItem) -> MedicationSourceReference:
    return MedicationSourceReference.model_validate(item)


def _source_from_rule(rule: MedicationDoseRule) -> MedicationSourceReference:
    return MedicationSourceReference.model_validate(rule)


def _dose_warning_message(rule: MedicationDoseRule, dose_value: Decimal) -> str:
    parts = [f"Dosis {dose_value} fuera del rango curado"]
    if rule.min_value is not None or rule.max_value is not None:
        parts.append(f"({rule.min_value or '-'}-{rule.max_value or '-'} {rule.unit or ''})")
    if rule.avoid_dose_text:
        parts.append(rule.avoid_dose_text)
    return " ".join(parts).strip()
