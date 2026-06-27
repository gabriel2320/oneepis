from __future__ import annotations

from oneepis_api.models.clinical_record import ClinicalEventSourceType
from oneepis_api.models.lab import LabPanel, LabResult
from oneepis_api.schemas.clinical_record import LabPanelRead, LabResultRead, LabResultSourceRead
from oneepis_api.schemas.clinical_record_contracts.lab import LabPanelBase, LabResultBase


def lab_source_label(
    source_type: ClinicalEventSourceType,
    source_ref: str | None,
) -> str:
    labels = {
        ClinicalEventSourceType.MANUAL: "Registro manual",
        ClinicalEventSourceType.CLINICAL_ENTRY: "Nota clinica",
        ClinicalEventSourceType.VITAL_SIGN: "Signo vital",
        ClinicalEventSourceType.IMPORTED_DOCUMENT: "Documento importado",
        ClinicalEventSourceType.AI_DRAFT: "Borrador IA",
    }
    base = labels.get(source_type, source_type.value)
    if source_ref:
        return f"{base} ({source_ref})"
    return base


def build_lab_result_source(panel: LabPanel, result: LabResult) -> LabResultSourceRead:
    request_path = (
        f"/api/v1/patients/{panel.patient_id}/lab-panels/{panel.id}/results/{result.id}"
    )
    return LabResultSourceRead(
        source_type=panel.source_type,
        source_ref=panel.source_ref,
        panel_id=panel.id,
        panel_name=panel.panel_name,
        request_path=request_path,
        label=lab_source_label(panel.source_type, panel.source_ref),
    )


def serialize_lab_result(panel: LabPanel, result: LabResult) -> LabResultRead:
    base = LabResultBase.model_validate(result, from_attributes=True).model_dump()
    return LabResultRead(
        **base,
        id=result.id,
        panel_id=result.panel_id,
        patient_id=result.patient_id,
        source=build_lab_result_source(panel, result),
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


def serialize_lab_panel(panel: LabPanel) -> LabPanelRead:
    base = LabPanelBase.model_validate(panel, from_attributes=True).model_dump()
    return LabPanelRead(
        **base,
        id=panel.id,
        patient_id=panel.patient_id,
        results=[serialize_lab_result(panel, result) for result in panel.results],
        created_at=panel.created_at,
        updated_at=panel.updated_at,
    )
