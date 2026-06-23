from __future__ import annotations

import re

from oneepis_api.models.clinical_record import (
    ClinicalEntry,
    ClinicalEventSourceType,
    ClinicalEventType,
)
from oneepis_api.schemas.clinical_record import (
    ClinicalPatch,
    ClinicalPatchOperation,
    ClinicalPatchSource,
    EventProposalFromEntry,
    EventProposalsFromEntryResponse,
)

SECTION_EVENT_TYPES: dict[str, ClinicalEventType] = {
    "subjective": ClinicalEventType.CLINICAL_NOTE,
    "objective": ClinicalEventType.CLINICAL_NOTE,
    "assessment": ClinicalEventType.CLINICAL_NOTE,
    "plan": ClinicalEventType.CARE_PLAN,
}

SECTION_LABELS = {
    "subjective": "Subjetivo",
    "objective": "Objetivo",
    "assessment": "Evaluacion",
    "plan": "Plan",
}


def propose_events_from_entry(
    entry: ClinicalEntry,
    *,
    max_proposals: int,
) -> EventProposalsFromEntryResponse:
    proposals: list[EventProposalFromEntry] = []
    warnings: list[str] = []

    for section in ("assessment", "plan", "subjective", "objective"):
        text = getattr(entry, section)
        if not text:
            continue
        for index, summary in enumerate(_candidate_summaries(text), start=1):
            if len(proposals) >= max_proposals:
                break
            proposal_id = f"{entry.id}:{section}:{index}"
            source_ref = str(entry.id)
            proposal_payload = {
                "source_entry_id": str(entry.id),
                "source_entry_title": entry.title,
                "source_section": section,
                "source_section_label": SECTION_LABELS[section],
                "proposal_only": True,
            }
            proposals.append(
                EventProposalFromEntry(
                    proposal_id=proposal_id,
                    event_type=SECTION_EVENT_TYPES[section],
                    occurred_at=entry.occurred_at,
                    summary=summary,
                    source_type=ClinicalEventSourceType.CLINICAL_ENTRY,
                    source_ref=source_ref,
                    payload=proposal_payload,
                    evidence_label=f"{entry.title} / {SECTION_LABELS[section]}",
                    patch=_build_event_patch(
                        proposal_id=proposal_id,
                        entry=entry,
                        section=section,
                        summary=summary,
                        source_ref=source_ref,
                        payload=proposal_payload,
                    ),
                )
            )
        if len(proposals) >= max_proposals:
            break

    if not proposals:
        warnings.append(
            "La evolucion no contiene secciones SOAP suficientes para proponer eventos."
        )
    if _section_count(entry) == 0:
        warnings.append("No se reviso texto libre fuera de secciones estructuradas.")
    if len(proposals) >= max_proposals:
        warnings.append("Se alcanzo el limite de propuestas; revisa la evolucion completa.")

    return EventProposalsFromEntryResponse(
        entry_id=entry.id,
        entry_title=entry.title,
        proposals=proposals,
        warnings=warnings,
    )


def _build_event_patch(
    *,
    proposal_id: str,
    entry: ClinicalEntry,
    section: str,
    summary: str,
    source_ref: str,
    payload: dict[str, str | bool],
) -> ClinicalPatch:
    reason = f"Extraido desde {entry.title} / {SECTION_LABELS[section]}"
    return ClinicalPatch(
        patch_id=proposal_id,
        target="clinical_event",
        mode="suggestion",
        operations=[
            ClinicalPatchOperation(
                op="add",
                path="/event_type",
                value=SECTION_EVENT_TYPES[section].value,
                reason=reason,
            ),
            ClinicalPatchOperation(
                op="add",
                path="/occurred_at",
                value=entry.occurred_at,
                reason="Usa la fecha de ocurrencia de la evolucion fuente.",
            ),
            ClinicalPatchOperation(
                op="add",
                path="/summary",
                value=summary,
                reason=reason,
            ),
            ClinicalPatchOperation(
                op="add",
                path="/source_type",
                value=ClinicalEventSourceType.CLINICAL_ENTRY.value,
                reason="Mantiene trazabilidad hacia la evolucion fuente.",
            ),
            ClinicalPatchOperation(
                op="add",
                path="/source_ref",
                value=source_ref,
                reason="Identificador de la evolucion fuente.",
            ),
            ClinicalPatchOperation(
                op="add",
                path="/payload",
                value=payload,
                reason="Metadatos de seccion y propuesta para auditoria.",
            ),
        ],
        sources=[
            ClinicalPatchSource(
                source_type="clinical_entry",
                source_id=entry.id,
                label=f"{entry.title} / {SECTION_LABELS[section]}",
            )
        ],
        requires_human_confirmation=True,
    )


def _candidate_summaries(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    parts = re.split(r"(?:\n+|;|\. )", stripped)
    summaries: list[str] = []
    for part in parts:
        part = re.sub(r"\s+", " ", part)
        cleaned = part.strip(" .:-")
        if len(cleaned) < 8:
            continue
        summaries.append(_truncate_summary(cleaned))
    return summaries[:4]


def _truncate_summary(value: str) -> str:
    if len(value) <= 280:
        return value
    return f"{value[:277].rstrip()}..."


def _section_count(entry: ClinicalEntry) -> int:
    return sum(
        1
        for section in ("subjective", "objective", "assessment", "plan")
        if getattr(entry, section)
    )
