from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.clinical_record import ClinicalEncounter, RecordStatus
from oneepis_api.models.lab import LabPanel, LabResult, LabResultFlag
from oneepis_api.schemas.clinical_record import AssistantTimelineItem

from .patient_assistant_labs import lab_result_source_path


def fetch_lab_results_for_timeline(
    session: Session,
    patient_id: uuid.UUID,
    limit: int,
) -> list[LabResult]:
    statement = (
            select(LabResult)
            .join(LabPanel)
            .options(selectinload(LabResult.panel).selectinload(LabPanel.encounter))
        .where(
            LabResult.patient_id == patient_id,
            LabResult.status == RecordStatus.ACTIVE,
            LabPanel.status == RecordStatus.ACTIVE,
        )
        .order_by(LabPanel.occurred_at.desc(), LabResult.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def lab_timeline_items(
    patient_id: uuid.UUID,
    lab_results: list[LabResult],
) -> list[AssistantTimelineItem]:
    return [
        AssistantTimelineItem(
            item_type="lab_result",
            item_id=result.id,
            occurred_at=result.panel.occurred_at,
            label=result.name,
            summary=_lab_timeline_summary(result),
            source_label="lab_results",
            source_path=lab_result_source_path(patient_id, result.panel_id, result.id),
            **_encounter_metadata(result.panel.encounter),
        )
        for result in lab_results
    ]


def _lab_timeline_summary(result: LabResult) -> str:
    value = result.value
    if value is None and result.numeric_value is not None:
        value = str(result.numeric_value)
    value = value or "sin valor textual"
    unit = f" {result.unit}" if result.unit else ""
    flag = f" ({result.flag.value})" if result.flag != LabResultFlag.UNKNOWN else ""
    return _truncate(f"{result.panel.panel_name}: {value}{unit}{flag}")


def _truncate(value: str, max_length: int = 240) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."


def _encounter_metadata(encounter: ClinicalEncounter | None) -> dict[str, object]:
    if encounter is None:
        return {"scope": "longitudinal"}
    return {
        "encounter_id": encounter.id,
        "encounter_type": encounter.type,
        "encounter_status": encounter.status,
        "scope": encounter.type.value if encounter.type.value != "unknown" else "unknown",
    }
