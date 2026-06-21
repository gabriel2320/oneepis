from __future__ import annotations

import json
from typing import Literal, cast

from oneepis_api.schemas.ai import ClinicalAiSuggestion


def parse_json_content(content: str) -> dict[str, object]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return {}

    return value if isinstance(value, dict) else {}


def as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def parse_suggestions(value: object, *, source: str) -> list[ClinicalAiSuggestion]:
    if not isinstance(value, list):
        return []

    suggestions: list[ClinicalAiSuggestion] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        detail = str(item.get("detail") or "").strip()
        severity = _severity(item.get("severity"))
        action_label = item.get("action_label")
        if not title or not detail:
            continue
        suggestions.append(
            ClinicalAiSuggestion(
                title=title,
                detail=detail,
                severity=severity,
                source=cast(Literal["ollama", "local_rules"], source),
                action_label=str(action_label).strip() if action_label else None,
            )
        )
    return suggestions[:8]


def _severity(value: object) -> Literal["info", "warning", "critical"]:
    severity = str(value or "info").strip()
    if severity in {"info", "warning", "critical"}:
        return cast(Literal["info", "warning", "critical"], severity)
    return "info"
