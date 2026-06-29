from __future__ import annotations

import json
import uuid
from functools import lru_cache
from importlib import resources
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from oneepis_api.models.medication_catalog import (
    MedicationCatalogItem,
    MedicationCatalogStatus,
    MedicationSourceReviewStatus,
    MedicationSourceSystem,
)

FARMACO_SOURCE_LABEL = "Farmaco TXT local derivado"
FARMACO_SOURCE_VERSION = "farmaco-txt-derived-v1"
FARMACO_CURATED_BY = "oneepis.farmaco_txt"
FARMACO_CANDIDATE_COUNT = 944
FARMACO_ACCEPTED_COUNT = 915
FARMACO_EVIDENCE_TAG_PREFIX = "farmaco_evidence:"
FARMACO_PRIORITY_TAG_PREFIX = "farmaco_priority:"

FarmacoArtifact = dict[str, Any]
FarmacoCandidate = dict[str, Any]


@lru_cache(maxsize=1)
def load_farmaco_candidates_artifact() -> FarmacoArtifact:
    return _load_data_json("farmaco_candidates.json")


@lru_cache(maxsize=1)
def load_farmaco_candidate_evidence_artifact() -> FarmacoArtifact:
    return _load_data_json("farmaco_candidate_evidence.json")


@lru_cache(maxsize=1)
def load_farmaco_source_map() -> FarmacoArtifact:
    return _load_data_json("farmaco_source_map.json")


@lru_cache(maxsize=1)
def farmaco_evidence_by_catalog_id() -> dict[uuid.UUID, FarmacoCandidate]:
    artifact = load_farmaco_candidate_evidence_artifact()
    return {
        uuid.UUID(str(item["catalog_item_id"])): item
        for item in artifact.get("items", [])
        if item.get("catalog_item_id")
    }


def accepted_farmaco_candidates() -> list[FarmacoCandidate]:
    artifact = load_farmaco_candidates_artifact()
    return [
        candidate
        for candidate in artifact.get("candidates", [])
        if candidate.get("decision") == "accepted"
    ]


def farmaco_evidence_for_catalog_item_id(
    item_id: uuid.UUID | str | None,
) -> FarmacoCandidate | None:
    if item_id is None:
        return None
    return farmaco_evidence_by_catalog_id().get(uuid.UUID(str(item_id)))


def farmaco_candidate_by_display_name(display_name: str) -> FarmacoCandidate | None:
    normalized = _normalize_name(display_name)
    for candidate in load_farmaco_candidates_artifact().get("candidates", []):
        if _normalize_name(str(candidate.get("display_name") or "")) == normalized:
            return candidate
    return None


def ensure_farmaco_draft_catalog(session: Session) -> None:
    candidates = accepted_farmaco_candidates()
    accepted_by_id = {
        uuid.UUID(str(candidate["catalog_item_id"])): candidate for candidate in candidates
    }
    existing_items = list(
        session.scalars(
            select(MedicationCatalogItem)
            .options(selectinload(MedicationCatalogItem.dose_rules))
            .where(MedicationCatalogItem.source_label == FARMACO_SOURCE_LABEL)
        )
    )
    existing_by_id = {item.id: item for item in existing_items}

    for item in existing_items:
        if item.review_status != MedicationSourceReviewStatus.DRAFT:
            continue
        candidate = accepted_by_id.get(item.id)
        if candidate is None:
            item.status = MedicationCatalogStatus.UNAVAILABLE
            item.review_status = MedicationSourceReviewStatus.DEPRECATED
            continue
        _apply_farmaco_draft_metadata(item, candidate)

    for item_id, candidate in accepted_by_id.items():
        if item_id in existing_by_id:
            continue
        session.add(_farmaco_catalog_item(item_id, candidate))
    session.flush()


def _farmaco_catalog_item(
    item_id: uuid.UUID,
    candidate: FarmacoCandidate,
) -> MedicationCatalogItem:
    item = MedicationCatalogItem(
        id=item_id,
        display_name=str(candidate["display_name"]),
        generic_name=str(candidate["generic_name"]),
        status=MedicationCatalogStatus.DRAFT,
        source_system=MedicationSourceSystem.LOCAL_CURATED,
        source_label=FARMACO_SOURCE_LABEL,
        source_version=FARMACO_SOURCE_VERSION,
        external_id=f"farmaco-txt:{item_id}",
        curated_by=FARMACO_CURATED_BY,
        review_status=MedicationSourceReviewStatus.DRAFT,
    )
    _apply_farmaco_draft_metadata(item, candidate)
    return item


def _apply_farmaco_draft_metadata(
    item: MedicationCatalogItem,
    candidate: FarmacoCandidate,
) -> None:
    item.display_name = str(candidate["display_name"])
    item.generic_name = str(candidate["generic_name"])
    item.form = None
    item.strength = None
    item.route = None
    item.status = MedicationCatalogStatus.DRAFT
    item.tags = _catalog_tags(candidate)
    item.clinical_uses = []
    item.administration_routes = []
    item.interaction_alerts = []
    item.safety_alerts = []
    item.monitoring_notes = []
    item.source_system = MedicationSourceSystem.LOCAL_CURATED
    item.source_label = FARMACO_SOURCE_LABEL
    item.source_url = None
    item.external_id = f"farmaco-txt:{candidate['catalog_item_id']}"
    item.source_version = FARMACO_SOURCE_VERSION
    item.retrieved_at = None
    item.curated_by = FARMACO_CURATED_BY
    item.reviewed_at = None
    item.review_status = MedicationSourceReviewStatus.DRAFT
    item.dose_rules = []


def _catalog_tags(candidate: FarmacoCandidate) -> list[str]:
    evidence = farmaco_evidence_for_catalog_item_id(candidate.get("catalog_item_id"))
    tags = list(candidate.get("tags") or [])
    if evidence and evidence.get("mention_count"):
        tags.append("farmaco_txt_evidence")
    for tag in evidence.get("evidence_tags", []) if evidence else []:
        tags.append(f"{FARMACO_EVIDENCE_TAG_PREFIX}{tag}")
    for tag in candidate.get("priority_tags") or []:
        tags.append(f"{FARMACO_PRIORITY_TAG_PREFIX}{tag}")
    return _stable_unique_tags(tags)


def _stable_unique_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for tag in tags:
        normalized = str(tag).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def _load_data_json(filename: str) -> FarmacoArtifact:
    resource = resources.files("oneepis_api.data").joinpath(filename)
    return json.loads(resource.read_text(encoding="utf-8"))


def _normalize_name(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").split())
