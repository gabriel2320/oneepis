from __future__ import annotations

import uuid
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from oneepis_api.schemas.assistant import (
    AssistantCorrelationFinding,
    AssistantCorrelationPreset,
    AssistantCorrelationRequest,
    AssistantCorrelationResponse,
    AssistantTimelineItem,
)
from oneepis_api.services.assistant_timeline import build_assistant_timeline

DEFAULT_CORRELATION_PRESETS: tuple[AssistantCorrelationPreset, ...] = (
    "fever_infection",
    "renal_medications",
    "respiratory_oxygen",
    "hemoglobin_bleeding",
    "medication_changes",
)
TEXT_TRANSLATION = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouaeiounn")


def build_assistant_correlations(
    session: Session,
    patient_id: uuid.UUID,
    payload: AssistantCorrelationRequest,
) -> AssistantCorrelationResponse:
    presets = _unique_presets(payload.presets or list(DEFAULT_CORRELATION_PRESETS))
    timeline = build_assistant_timeline(session, patient_id, limit=100)
    findings: list[AssistantCorrelationFinding] = []
    missing: list[str] = []

    for preset in presets:
        finding = _correlate_preset(preset, timeline.items, payload.limit)
        if finding is None:
            missing.append(_correlation_missing_message(preset))
            continue
        findings.append(finding)

    return AssistantCorrelationResponse(
        patient_id=patient_id,
        findings=findings[: payload.limit],
        missing=missing,
        limits=[
            "Correlacion deterministica de solo lectura; no diagnostica ni prescribe.",
            "Solo relaciona fuentes existentes por presets cerrados y texto estructurado.",
            f"Respuesta limitada a {payload.limit} hallazgo(s).",
        ],
    )


def _unique_presets(
    presets: list[AssistantCorrelationPreset],
) -> list[AssistantCorrelationPreset]:
    unique: list[AssistantCorrelationPreset] = []
    for preset in presets:
        if preset not in unique:
            unique.append(preset)
    return unique


def _correlate_preset(
    preset: AssistantCorrelationPreset,
    items: list[AssistantTimelineItem],
    limit: int,
) -> AssistantCorrelationFinding | None:
    if preset == "fever_infection":
        fever = _filter_items(items, keywords=("fiebre", "febril", "temperatura"))
        fever.extend(
            item
            for item in items
            if item.source_type == "vital_sign"
            and _payload_or_summary_has_temperature(item, minimum=38.0)
            and item not in fever
        )
        infection = _filter_items(
            items,
            keywords=(
                "infecc",
                "pcr",
                "proteina c reactiva",
                "leucoc",
                "cultivo",
                "antibiot",
            ),
        )
        return _finding_if_sources(
            preset=preset,
            title="Fiebre e infeccion",
            summary=(
                "Fuentes con fiebre o temperatura elevada aparecen junto a fuentes "
                "infecciosas o inflamatorias."
            ),
            groups=[fever, infection],
            missing=["Faltan fiebre documentada.", "Faltan fuentes infecciosas o inflamatorias."],
            limit=limit,
        )

    if preset == "renal_medications":
        renal = _filter_items(
            items,
            keywords=("renal", "creatinina", "clearance", "egfr", "filtrado glomerular"),
        )
        medications = [item for item in items if item.source_type == "medication"]
        return _finding_if_sources(
            preset=preset,
            title="Funcion renal y medicamentos",
            summary="Fuentes renales aparecen junto a medicacion activa registrada.",
            groups=[renal, medications],
            missing=["Faltan fuentes renales.", "Falta medicacion activa."],
            limit=limit,
        )

    if preset == "respiratory_oxygen":
        respiratory = _filter_items(
            items,
            keywords=("disnea", "respiratorio", "sato2", "saturacion", "hipox", "fr "),
        )
        respiratory.extend(
            item
            for item in items
            if item.source_type == "vital_sign"
            and (_payload_or_summary_has_saturation(item, maximum=92.0) or "FR " in item.summary)
            and item not in respiratory
        )
        oxygen = _filter_items(items, keywords=("oxigen", "naricera", "fio2", "ventil"))
        return _finding_if_sources(
            preset=preset,
            title="Respiratorio y oxigeno",
            summary=(
                "Fuentes respiratorias o de saturacion baja aparecen junto a registros "
                "de oxigeno o soporte ventilatorio."
            ),
            groups=[respiratory, oxygen],
            missing=[
                "Faltan fuentes respiratorias.",
                "Faltan fuentes de oxigeno o soporte ventilatorio.",
            ],
            limit=limit,
        )

    if preset == "hemoglobin_bleeding":
        hemoglobin = _filter_items(
            items,
            keywords=("hemoglobina", "hematocrito", " hb ", "anemia"),
        )
        bleeding = _filter_items(
            items,
            keywords=("sangrado", "hemorrag", "melena", "hematemesis", "rectorragia"),
        )
        return _finding_if_sources(
            preset=preset,
            title="Hemoglobina y sangrado",
            summary=(
                "Fuentes hematologicas aparecen junto a registros compatibles con "
                "sangrado documentado."
            ),
            groups=[hemoglobin, bleeding],
            missing=["Faltan fuentes de hemoglobina o hematocrito.", "Faltan fuentes de sangrado."],
            limit=limit,
        )

    medication_items = [item for item in items if item.source_type == "medication"]
    medication_events = [
        item
        for item in _filter_items(items, keywords=("inicia", "suspende", "ajusta", "cambia"))
        if item.source_type in {"clinical_event", "clinical_entry", "medication"}
    ]
    sources = _dedupe_items([*medication_events, *medication_items])[:limit]
    if len(sources) < 2:
        return None
    return AssistantCorrelationFinding(
        preset="medication_changes",
        title="Cambios de medicacion",
        summary=(
            "Hay multiples fuentes de medicacion o cambios narrativos que conviene "
            "revisar en orden temporal."
        ),
        sources=sources,
        missing=[],
    )


def _finding_if_sources(
    *,
    preset: AssistantCorrelationPreset,
    title: str,
    summary: str,
    groups: list[list[AssistantTimelineItem]],
    missing: list[str],
    limit: int,
) -> AssistantCorrelationFinding | None:
    present_groups = [group for group in groups if group]
    if len(present_groups) != len(groups):
        return None
    sources = _dedupe_items([item for group in groups for item in group])[:limit]
    return AssistantCorrelationFinding(
        preset=preset,
        title=title,
        summary=summary,
        sources=sources,
        missing=[] if sources else missing,
    )


def _filter_items(
    items: list[AssistantTimelineItem],
    *,
    keywords: tuple[str, ...],
) -> list[AssistantTimelineItem]:
    normalized_keywords = tuple(_normalize_text(keyword) for keyword in keywords)
    matches = []
    for item in items:
        haystack = _normalize_text(
            " ".join(
                _compact(
                    [
                        item.label,
                        item.summary,
                        item.status,
                        " ".join(item.details),
                        _payload_text(item.payload),
                    ]
                )
            )
        )
        if any(keyword in haystack for keyword in normalized_keywords):
            matches.append(item)
    return matches


def _dedupe_items(items: list[AssistantTimelineItem]) -> list[AssistantTimelineItem]:
    seen: set[tuple[str, uuid.UUID]] = set()
    unique = []
    for item in items:
        key = (item.source_type, item.source_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    unique.sort(key=_sort_key, reverse=True)
    return unique


def _sort_key(item: AssistantTimelineItem) -> datetime:
    if item.occurred_at is not None:
        if item.occurred_at.tzinfo is not None:
            return item.occurred_at
        return item.occurred_at.replace(tzinfo=UTC)
    if item.occurred_on is not None:
        return datetime.combine(item.occurred_on, time.min, tzinfo=UTC)
    return datetime.min.replace(tzinfo=UTC)


def _payload_or_summary_has_temperature(
    item: AssistantTimelineItem,
    *,
    minimum: float,
) -> bool:
    value = _payload_number(item.payload)
    if value is not None and value >= minimum:
        return True
    summary_value = _number_after_label(item.summary, "T")
    return summary_value is not None and summary_value >= minimum


def _payload_or_summary_has_saturation(
    item: AssistantTimelineItem,
    *,
    maximum: float,
) -> bool:
    value = _payload_number(item.payload)
    if value is not None and value <= maximum:
        return True
    summary_value = _number_after_label(item.summary, "SatO2")
    return summary_value is not None and summary_value <= maximum


def _number_after_label(value: str, label: str) -> float | None:
    marker = f"{label} "
    if marker not in value:
        return None
    tail = value.split(marker, 1)[1].split(" ", 1)[0].replace(",", ".")
    try:
        return float(tail)
    except ValueError:
        return None


def _correlation_missing_message(preset: AssistantCorrelationPreset) -> str:
    messages = {
        "fever_infection": "No hay suficientes fuentes para correlacionar fiebre e infeccion.",
        "renal_medications": (
            "No hay suficientes fuentes para correlacionar funcion renal y medicamentos."
        ),
        "respiratory_oxygen": (
            "No hay suficientes fuentes para correlacionar respiratorio y oxigeno."
        ),
        "hemoglobin_bleeding": (
            "No hay suficientes fuentes para correlacionar hemoglobina y sangrado."
        ),
        "medication_changes": (
            "No hay suficientes fuentes para correlacionar cambios de medicacion."
        ),
    }
    return messages[preset]


def _payload_number(payload: dict[str, Any]) -> float | None:
    for key in ("value", "result", "numeric_value"):
        value = payload.get(key)
        if isinstance(value, Decimal | int | float):
            return float(value)
        if isinstance(value, str):
            normalized = value.strip().replace(",", ".")
            try:
                return float(normalized)
            except ValueError:
                continue
    return None


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
    return value.translate(TEXT_TRANSLATION).casefold()


def _compact(values: list[Any]) -> list[str]:
    return [str(value).strip() for value in values if str(value or "").strip()]
