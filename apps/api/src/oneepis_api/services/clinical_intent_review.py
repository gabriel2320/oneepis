from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from oneepis_api.models.audit import AuditEvent
from oneepis_api.schemas.clinical_record import ClinicalReviewItem
from oneepis_api.schemas.patient import PatientRecordSnapshot
from oneepis_api.services.clinical_intent_text import payload_text as _payload_text
from oneepis_api.services.clinical_problem_context import event_matches_any_problem
from oneepis_api.services.medication_catalog_farmaco import farmaco_evidence_for_catalog_item_id

ReviewDecisionMetadata = dict[str, object]
FARMACO_REVIEW_TAGS = {"renal", "hepatica", "embarazo", "lactancia", "interaccion"}


def build_review_items(
    snapshot: PatientRecordSnapshot,
    events: list[object],
    baseline_entry: object | None,
) -> list[ClinicalReviewItem]:
    items: list[ClinicalReviewItem] = []
    for medication in snapshot.active_medications[:12]:
        if not medication.dose:
            items.append(
                ClinicalReviewItem(
                    item_type="missing_medication_dose",
                    label=f"{medication.name}: falta dosis",
                    detail="Medicamento activo sin dosis estructurada.",
                    source_type="medication",
                    source_id=medication.id,
                    suggested_action="Completar dosis o confirmar que no aplica.",
                )
            )
        if not medication.frequency:
            items.append(
                ClinicalReviewItem(
                    item_type="missing_medication_frequency",
                    label=f"{medication.name}: falta frecuencia",
                    detail="Medicamento activo sin frecuencia estructurada.",
                    source_type="medication",
                    source_id=medication.id,
                    suggested_action="Completar frecuencia o confirmar que no aplica.",
                )
            )
        farmaco_review = _farmaco_txt_review_item(medication)
        if farmaco_review is not None:
            items.append(farmaco_review)

    compared_med_events = [
        event
        for event in events[:12]
        if getattr(event.event_type, "value", event.event_type) == "medication"
        and (baseline_entry is None or event.occurred_at > baseline_entry.occurred_at)
    ]
    for event in compared_med_events:
        if not medication_payload_has_minimum(event.payload):
            items.append(
                ClinicalReviewItem(
                    item_type="unstructured_medication_event",
                    label="Evento de medicacion incompleto",
                    detail=event.summary,
                    source_type="clinical_event",
                    source_id=event.id,
                    suggested_action="Completar payload con action y name/medication.",
                )
            )
        if not event_matches_any_problem(snapshot, event):
            items.append(
                ClinicalReviewItem(
                    item_type="unlinked_medication_event",
                    label="Evento de medicacion sin problema asociado",
                    detail=event.summary,
                    source_type="clinical_event",
                    source_id=event.id,
                    suggested_action="Vincular a un problema activo o crear uno si corresponde.",
                )
            )
    return items


def apply_review_decisions(
    session: Session,
    patient_id: uuid.UUID,
    items: list[ClinicalReviewItem],
) -> list[ClinicalReviewItem]:
    if not items:
        return items
    decisions = _review_decision_map(session, patient_id)
    if not decisions:
        return items
    applied: list[ClinicalReviewItem] = []
    for item in items:
        fingerprint = review_item_fingerprint(
            item_type=item.item_type,
            source_type=item.source_type,
            source_id=item.source_id,
            label=item.label,
        )
        legacy_key = _review_item_key(
            item_type=item.item_type,
            source_type=item.source_type,
            source_id=item.source_id,
            label=item.label,
        )
        decision = decisions.get(fingerprint) or decisions.get(legacy_key)
        if decision:
            item = item.model_copy(
                update={
                    "decision_status": decision["status"],
                    "decision_actor_id": decision["actor_id"],
                    "decision_at": decision["created_at"],
                    "decision_audit_event_id": decision["audit_event_id"],
                }
            )
        applied.append(item)
    return applied


def medication_payload_has_minimum(payload: dict[str, object]) -> bool:
    return _payload_text(payload.get("action")) is not None and (
        _payload_text(payload.get("name")) is not None
        or _payload_text(payload.get("medication")) is not None
    )


def _farmaco_txt_review_item(medication: object) -> ClinicalReviewItem | None:
    evidence = farmaco_evidence_for_catalog_item_id(getattr(medication, "catalog_item_id", None))
    if not evidence or evidence.get("decision") != "accepted":
        return None
    tags = sorted(FARMACO_REVIEW_TAGS.intersection(set(evidence.get("evidence_tags") or [])))
    if not tags:
        return None
    pages = _review_pages(evidence.get("pages"))
    return ClinicalReviewItem(
        item_type="unstructured_medication_event",
        label=f"{medication.name}: revisar evidencia TXT Farmaco",
        detail=(
            "Ficha Farmaco draft con evidencia contextual pendiente de curacion humana; "
            f"temas: {', '.join(tags)}; {pages}. "
            "No se convirtio en alerta clinica, uso ni monitoreo automatico."
        ),
        source_type="medication",
        source_id=medication.id,
        suggested_action=(
            "Revisar fuente TXT antes de convertirla en alerta, uso o monitoreo curado."
        ),
    )


def _review_pages(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "paginas sin detalle"
    pages = [str(item) for item in value[:6]]
    if len(value) > 6:
        pages.append("...")
    return f"paginas: {', '.join(pages)}"


def _review_decision_map(
    session: Session,
    patient_id: uuid.UUID,
) -> dict[str, ReviewDecisionMetadata]:
    statement = (
        select(AuditEvent)
        .where(
            AuditEvent.action == "ai.review_item.decided",
            AuditEvent.entity_type == "patient",
            AuditEvent.entity_id == patient_id,
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(100)
    )
    decisions: dict[str, ReviewDecisionMetadata] = {}
    for audit_event in session.scalars(statement):
        metadata = audit_event.extra_data
        decision = metadata.get("decision")
        if decision not in {"accepted", "rejected"}:
            continue
        key = str(metadata.get("item_fingerprint") or "")
        if not key:
            key = _review_item_key(
                item_type=str(metadata.get("item_type") or ""),
                source_type=str(metadata.get("source_type") or ""),
                source_id=metadata.get("source_id"),
                label=str(metadata.get("label") or ""),
            )
        decisions.setdefault(
            key,
            {
                "status": decision,
                "actor_id": audit_event.actor_id,
                "created_at": audit_event.created_at,
                "audit_event_id": audit_event.id,
            },
        )
    return decisions


def review_item_fingerprint(
    *,
    item_type: str,
    source_type: str,
    source_id: uuid.UUID | str | None,
    label: str,
) -> str:
    key = _review_item_key(
        item_type=item_type,
        source_type=source_type,
        source_id=source_id,
        label=label.strip(),
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _review_item_key(
    *,
    item_type: str,
    source_type: str,
    source_id: uuid.UUID | str | None,
    label: str,
) -> str:
    return "|".join([item_type, source_type, str(source_id or ""), label])
