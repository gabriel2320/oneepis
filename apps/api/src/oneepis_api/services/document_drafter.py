from __future__ import annotations

from oneepis_api.schemas.clinical_record import (
    ClinicalEventSource,
    DraftSoapFromEventsResponse,
    DraftSoapSectionSource,
)
from oneepis_api.services.clinical_context import ClinicalEventContext


def draft_soap_from_events(
    context: ClinicalEventContext,
    *,
    provider: str,
    ai_available: bool,
) -> DraftSoapFromEventsResponse:
    events = context.events
    patient = context.snapshot.patient
    warnings: list[str] = []
    if not ai_available:
        warnings.append("Ollama no esta disponible; se genero un borrador local por reglas.")
    if not events:
        warnings.append("No se encontraron eventos clinicos seleccionados para este paciente.")

    event_lines = [f"- {event.summary}" for event in events]
    vital_lines = [line for event in events for line in _event_payload_lines(event.payload)]
    problem_lines = [f"- {problem.title}" for problem in context.snapshot.active_problems[:5]]
    medication_lines = [
        f"- {med.name}{f' {med.dose}' if med.dose else ''}"
        for med in context.snapshot.active_medications[:5]
    ]

    subjective = "\n".join(event_lines) if event_lines else "Sin relato subjetivo nuevo registrado."
    objective_parts = vital_lines or ["Sin hallazgos objetivos estructurados nuevos."]
    if context.snapshot.latest_vitals is not None:
        vital = context.snapshot.latest_vitals
        objective_parts.append(
            "Ultimos signos: "
            f"FC {vital.heart_rate_bpm or '-'}, "
            f"PA {vital.systolic_bp or '-'}/{vital.diastolic_bp or '-'}, "
            f"Sat {vital.oxygen_saturation_pct or '-'}."
        )

    assessment_parts = problem_lines or ["Paciente en seguimiento clinico."]
    plan_parts = medication_lines or ["Revisar eventos, completar indicaciones y confirmar plan."]
    section_sources = _section_sources(context)

    return DraftSoapFromEventsResponse(
        title=f"Evolucion SOAP - {patient.first_name} {patient.last_name}",
        subjective=subjective,
        objective="\n".join(objective_parts),
        assessment="\n".join(assessment_parts),
        plan="\n".join(plan_parts),
        sources=[
            ClinicalEventSource(clinical_event_id=event.id, label=event.summary) for event in events
        ],
        section_sources=section_sources,
        warnings=warnings,
        ai_available=ai_available,
        provider=provider,
        requires_human_confirmation=True,
    )


def _event_payload_lines(payload: dict[str, object]) -> list[str]:
    lines: list[str] = []
    for key, value in payload.items():
        if value in (None, "", []):
            continue
        label = key.replace("_", " ")
        lines.append(f"{label}: {value}")
    return lines[:8]


def _section_sources(context: ClinicalEventContext) -> list[DraftSoapSectionSource]:
    sources: list[DraftSoapSectionSource] = []
    for event in context.events:
        sources.append(
            DraftSoapSectionSource(
                section="subjective",
                source_type="clinical_event",
                source_id=event.id,
                label=event.summary,
                reason="Incluido como relato o hecho clinico seleccionado.",
            )
        )
        if event.payload:
            sources.append(
                DraftSoapSectionSource(
                    section="objective",
                    source_type="clinical_event",
                    source_id=event.id,
                    label=event.summary,
                    reason="Payload estructurado usado como dato objetivo.",
                )
            )

    if context.snapshot.latest_vitals is not None:
        vital = context.snapshot.latest_vitals
        sources.append(
            DraftSoapSectionSource(
                section="objective",
                source_type="vital_sign",
                source_id=vital.id,
                label="Ultimos signos vitales",
                reason="Ultimo control vital agregado al objetivo.",
            )
        )

    for problem in context.snapshot.active_problems[:5]:
        sources.append(
            DraftSoapSectionSource(
                section="assessment",
                source_type="problem",
                source_id=problem.id,
                label=problem.title,
                reason="Problema activo usado para analisis.",
            )
        )

    for medication in context.snapshot.active_medications[:5]:
        sources.append(
            DraftSoapSectionSource(
                section="plan",
                source_type="medication",
                source_id=medication.id,
                label=medication.name,
                reason="Medicacion activa usada como referencia de plan.",
            )
        )

    if not sources:
        sources.append(
            DraftSoapSectionSource(
                section="plan",
                source_type="structured_context",
                label="Contexto clinico estructurado",
                reason="Fallback local cuando no hay fuentes seleccionadas.",
            )
        )
    return sources
