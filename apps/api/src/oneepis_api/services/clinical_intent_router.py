from __future__ import annotations

from oneepis_api.schemas.clinical_record import (
    ClinicalIntentAction,
    ClinicalIntentRouteRequest,
    ClinicalIntentRouteResponse,
    ClinicalIntentType,
)
from oneepis_api.services.clinical_intent_actions import (
    clinical_intent_action as _action,
)
from oneepis_api.services.clinical_intent_text import normalize_text as _normalize_text


def route_clinical_intent(payload: ClinicalIntentRouteRequest) -> ClinicalIntentRouteResponse:
    text = _normalize_text(payload.text)
    direct_action = _direct_form_action(text, payload.text)
    if direct_action:
        return ClinicalIntentRouteResponse(
            recognized=True,
            original_text=payload.text,
            intent_type=None,
            mode="structured_proposal",
            confidence="moderate",
            explanation=(
                "Se reconocio una accion de registro. AI-Chart abrira un formulario existente; "
                "no se guardaran datos sin revision humana."
            ),
            suggested_actions=[direct_action],
            fallback_options=_fallback_actions(),
        )

    matches: list[tuple[ClinicalIntentType, str, tuple[str, ...]]] = [
        (
            "draft_soap",
            "draft",
            ("evolucion", "evoluciona", "soap", "nota de hoy", "prepara evolucion"),
        ),
        (
            "daily_changes",
            "read",
            ("cambio", "cambios", "desde ayer", "ultimas 24", "24h", "24 horas"),
        ),
        (
            "active_problems",
            "read",
            ("problemas", "diagnosticos activos", "problemas activos", "ordena problemas"),
        ),
        (
            "timeline",
            "read",
            ("timeline", "linea de tiempo", "hospitalizacion", "cronologia"),
        ),
        (
            "show_sources",
            "read",
            ("fuentes", "de donde", "auditoria", "trazabilidad"),
        ),
        (
            "summarize_patient",
            "read",
            ("resume", "resumen", "ordename", "ordename", "caso", "paciente"),
        ),
    ]
    for intent_type, mode, keywords in matches:
        if any(keyword in text for keyword in keywords):
            return ClinicalIntentRouteResponse(
                recognized=True,
                original_text=payload.text,
                intent_type=intent_type,
                mode=mode,
                confidence="high",
                explanation="Intencion reconocida por router clinico deterministico.",
                suggested_actions=[
                    _action(
                        "create_soap_draft"
                        if intent_type == "draft_soap"
                        else "review_sources",
                        _intent_label(intent_type),
                        "Ejecutar la intencion reconocida como accion revisable.",
                        requires_confirmation=intent_type == "draft_soap",
                    )
                ],
                fallback_options=_fallback_actions(),
            )

    return ClinicalIntentRouteResponse(
        recognized=False,
        original_text=payload.text,
        intent_type=None,
        mode="read",
        confidence="low",
        explanation="No se reconocio una intencion clinica segura. Elige una opcion dirigida.",
        suggested_actions=[],
        fallback_options=_fallback_actions(),
    )


def _intent_label(intent_type: ClinicalIntentType) -> str:
    labels = {
        "summarize_patient": "Resumir paciente",
        "daily_changes": "Comparar ultimas 24 h",
        "active_problems": "Mostrar problemas activos",
        "timeline": "Crear timeline",
        "draft_soap": "Preparar evolucion S/O/A/P",
        "show_sources": "Mostrar fuentes",
    }
    return labels[intent_type]


def _fallback_actions() -> list[ClinicalIntentAction]:
    return [
        _action("review_sources", "Resumir paciente", "Ver contexto clinico resumido."),
        _action("review_sources", "Que cambio desde ayer", "Comparar cambios recientes."),
        _action(
            "create_soap_draft",
            "Preparar evolucion SOAP",
            "Crear borrador editable con confirmacion humana.",
            requires_confirmation=True,
        ),
        _action("review_sources", "Mostrar fuentes", "Ver fuentes usadas por AI-Chart."),
    ]


def _direct_form_action(text: str, original_text: str) -> ClinicalIntentAction | None:
    form_actions: list[tuple[tuple[str, ...], str, str]] = [
        (
            ("medicacion", "medicamento", "farmaco", "receta"),
            "Registrar medicacion",
            "Abrir formulario de medicacion con origen AI-Chart revisable.",
        ),
        (
            ("alergia", "alergias", "alergico"),
            "Registrar alergia",
            "Abrir formulario de alergias con origen AI-Chart revisable.",
        ),
        (
            ("signos vitales", "control de signos", "presion", "saturacion", "temperatura"),
            "Registrar signos vitales",
            "Abrir formulario de signos vitales con origen AI-Chart revisable.",
        ),
    ]
    for keywords, label, description in form_actions:
        if any(keyword in text for keyword in keywords):
            return _action(
                "create_event",
                label,
                f"{description} Texto original: {original_text}",
                requires_confirmation=True,
            )
    return None
