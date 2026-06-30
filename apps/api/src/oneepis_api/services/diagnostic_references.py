from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from unicodedata import category, normalize

from oneepis_api.schemas.clinical_record_contracts.diagnostics import (
    DiagnosisCodeReference,
    DiagnosticReferenceSource,
)

DIAGNOSTIC_REFERENCE_SOURCE_LABEL = "Referencias diagnosticas locales curadas"
DIAGNOSTIC_REFERENCE_SOURCE_VERSION = "diagnostic-references-v1"


@dataclass(frozen=True)
class DiagnosticReference:
    reference_id: uuid.UUID
    title: str
    domain: str
    aliases: tuple[str, ...]
    coding_references: tuple[DiagnosisCodeReference, ...]
    reference_sources: tuple[DiagnosticReferenceSource, ...]
    clinical_use_limit: str

    @property
    def searchable_text(self) -> str:
        return normalize_diagnostic_text(
            " ".join([self.title, self.domain, *self.aliases])
        )


@lru_cache(maxsize=1)
def load_diagnostic_references() -> tuple[DiagnosticReference, ...]:
    artifact = _load_artifact()
    return tuple(_reference_from_item(item) for item in artifact.get("items", []))


def search_diagnostic_references(query: str, *, limit: int = 5) -> list[DiagnosticReference]:
    normalized_query = normalize_diagnostic_text(query)
    if len(normalized_query) < 2:
        return []
    scored = [
        (score, reference)
        for reference in load_diagnostic_references()
        if (score := _reference_score(reference, normalized_query)) > 0
    ]
    scored.sort(key=lambda item: (-item[0], item[1].title))
    return [reference for _score, reference in scored[:limit]]


def diagnostic_references_from_texts(
    texts: list[str],
    *,
    limit: int = 5,
) -> list[DiagnosticReference]:
    haystack = normalize_diagnostic_text(" ".join(texts))
    if len(haystack) < 2:
        return []
    scored = []
    for reference in load_diagnostic_references():
        matches = [
            alias
            for alias in reference.aliases
            if normalize_diagnostic_text(alias) in haystack
        ]
        if normalize_diagnostic_text(reference.title) in haystack:
            matches.append(reference.title)
        if matches:
            scored.append((len(set(matches)), reference))
    scored.sort(key=lambda item: (-item[0], item[1].title))
    return [reference for _score, reference in scored[:limit]]


def normalize_diagnostic_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    ascii_text = "".join(char for char in decomposed if category(char) != "Mn")
    return " ".join(ascii_text.replace("-", " ").split())


def _reference_score(reference: DiagnosticReference, normalized_query: str) -> int:
    score = 0
    if normalized_query in normalize_diagnostic_text(reference.title):
        score += 6
    for alias in reference.aliases:
        normalized_alias = normalize_diagnostic_text(alias)
        if normalized_query == normalized_alias:
            score += 8
        elif normalized_query in normalized_alias or normalized_alias in normalized_query:
            score += 3
    if normalized_query in reference.searchable_text:
        score += 1
    return score


def _reference_from_item(item: dict[str, object]) -> DiagnosticReference:
    return DiagnosticReference(
        reference_id=uuid.UUID(str(item["reference_id"])),
        title=str(item["title"]),
        domain=str(item["domain"]),
        aliases=tuple(str(alias) for alias in item.get("aliases", [])),
        coding_references=tuple(
            DiagnosisCodeReference.model_validate(reference)
            for reference in item.get("coding_references", [])
        ),
        reference_sources=tuple(
            DiagnosticReferenceSource.model_validate(source)
            for source in item.get("reference_sources", [])
        ),
        clinical_use_limit=str(item["clinical_use_limit"]),
    )


def _load_artifact() -> dict[str, object]:
    resource = resources.files("oneepis_api.data").joinpath("diagnostic_references.json")
    return json.loads(resource.read_text(encoding="utf-8"))
