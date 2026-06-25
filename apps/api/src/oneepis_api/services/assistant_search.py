from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from oneepis_api.schemas.assistant import (
    AssistantSearchMatch,
    AssistantSearchRequest,
    AssistantSearchResponse,
    AssistantTimelineItem,
)
from oneepis_api.services.assistant_timeline import build_assistant_timeline


def search_assistant_timeline(
    session: Session,
    patient_id: uuid.UUID,
    payload: AssistantSearchRequest,
) -> AssistantSearchResponse:
    timeline = build_assistant_timeline(session, patient_id, limit=100)
    allowed_source_types = set(payload.source_types)
    query = payload.query.strip()
    normalized_query = _normalize_text(query)
    matches: list[AssistantSearchMatch] = []

    for item in timeline.items:
        if allowed_source_types and item.source_type not in allowed_source_types:
            continue
        matched_fields, snippets = _match_item(item, normalized_query)
        if not matched_fields:
            continue
        matches.append(
            AssistantSearchMatch(
                item=item,
                matched_fields=matched_fields,
                snippets=snippets,
            )
        )
        if len(matches) >= payload.limit:
            break

    searched_source_types = payload.source_types or sorted(
        {item.source_type for item in timeline.items}
    )
    return AssistantSearchResponse(
        patient_id=patient_id,
        query=query,
        matches=matches,
        searched_source_types=searched_source_types,
        limits=[
            "Busqueda deterministica de solo lectura sobre fuentes normalizadas del timeline.",
            "No usa embeddings, RAG ni IA generativa; "
            "puede omitir sinonimos o negaciones complejas.",
            f"Respuesta limitada a {payload.limit} coincidencia(s).",
        ],
    )


def _match_item(item: AssistantTimelineItem, normalized_query: str) -> tuple[list[str], list[str]]:
    searchable_fields = {
        "label": item.label,
        "summary": item.summary,
        "status": item.status,
        "details": " ".join(item.details),
        "source_ref": item.source_ref,
        "payload": _payload_text(item.payload),
    }
    matched_fields: list[str] = []
    snippets: list[str] = []
    for field, raw_value in searchable_fields.items():
        value = str(raw_value or "").strip()
        if not value:
            continue
        if normalized_query not in _normalize_text(value):
            continue
        matched_fields.append(field)
        snippets.append(_snippet(value, normalized_query))
    return matched_fields, snippets[:3]


def _payload_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in payload.items():
        if isinstance(value, dict):
            parts.append(_payload_text(value))
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        else:
            parts.append(f"{key}: {value}")
    return " ".join(_compact(parts))


def _normalize_text(value: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "Á": "a",
            "É": "e",
            "Í": "i",
            "Ó": "o",
            "Ú": "u",
            "ñ": "n",
            "Ñ": "n",
        }
    )
    return value.translate(replacements).casefold()


def _snippet(value: str, normalized_query: str) -> str:
    normalized_value = _normalize_text(value)
    index = normalized_value.find(normalized_query)
    if index < 0:
        return value[:160]
    start = max(index - 50, 0)
    end = min(index + len(normalized_query) + 80, len(value))
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(value) else ""
    return f"{prefix}{value[start:end]}{suffix}"


def _compact(values: list[Any]) -> list[str]:
    return [str(value).strip() for value in values if str(value or "").strip()]
