from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from oneepis_api.models.medication_catalog import (
    MedicationCatalogItem,
    MedicationCatalogStatus,
    MedicationDoseRule,
    MedicationDoseSeverity,
    MedicationSourceReviewStatus,
    MedicationSourceSystem,
)

DEMO_ANALGESIC_ID = uuid.UUID("10000000-0000-4000-8000-000000000101")
DEMO_ANALGESIC_RULE_ID = uuid.UUID("10000000-0000-4000-8000-000000000201")
DEMO_CARDIO_ID = uuid.UUID("10000000-0000-4000-8000-000000000102")
DEMO_CARDIO_RULE_ID = uuid.UUID("10000000-0000-4000-8000-000000000202")
DEMO_SOURCE_LABEL = "Fixture demo OneEpis; no uso clinico"
DEMO_ANALGESIC_DETAILS = {
    "clinical_uses": [
        {
            "indication": "Dolor o fiebre demo",
            "population": "adult_general_demo",
            "notes": "Ejemplo no clinico para validar contrato y UI.",
        }
    ],
    "administration_routes": ["oral"],
    "interaction_alerts": [
        {
            "substance": "interaccion-demo",
            "effect": "Ejemplo informativo; no evalua interacciones reales.",
            "recommendation": "Requiere revision humana y fuente curada antes de uso clinico.",
            "severity": MedicationDoseSeverity.WARNING.value,
        }
    ],
    "safety_alerts": [
        {
            "title": "Alerta demo",
            "description": "No usar como recomendacion clinica real.",
            "action": "Mantener solo para desarrollo y pruebas.",
            "severity": MedicationDoseSeverity.INFO.value,
        }
    ],
    "monitoring_notes": ["Confirmar alergias, comorbilidades y fuente local antes de indicar."],
}
DEMO_CARDIO_DETAILS = {
    **DEMO_ANALGESIC_DETAILS,
    "clinical_uses": [
        {
            "indication": "Uso cardiovascular demo",
            "population": "adult_general_demo",
            "notes": "Ejemplo no clinico para validar busqueda y alertas.",
        }
    ],
    "monitoring_notes": ["Verificar presion arterial y contexto clinico en regla revisada."],
}


def ensure_demo_medication_catalog(session: Session) -> None:
    if session.get(MedicationCatalogItem, DEMO_ANALGESIC_ID) is not None:
        _ensure_demo_details(session)
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
        **DEMO_ANALGESIC_DETAILS,
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
        **DEMO_CARDIO_DETAILS,
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


def _ensure_demo_details(session: Session) -> None:
    for item_id, details in (
        (DEMO_ANALGESIC_ID, DEMO_ANALGESIC_DETAILS),
        (DEMO_CARDIO_ID, DEMO_CARDIO_DETAILS),
    ):
        item = session.get(MedicationCatalogItem, item_id)
        if item is None:
            continue
        for field, value in details.items():
            if not getattr(item, field):
                setattr(item, field, value)
