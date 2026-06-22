# OneEpis AI-Chart Core

AI-Chart Core convierte la ficha en memoria clinica activa expresada desde
eventos, no en formularios con IA agregada.

## Flujo

```text
paciente -> encuentro -> eventos clinicos -> contexto -> borrador SOAP
-> confirmacion humana -> auditoria
```

## Reglas

- PostgreSQL es la fuente de verdad.
- `clinical_events` registra hechos clinicos longitudinales.
- `clinical_entries` conserva documentos SOAP/evoluciones.
- La IA no firma.
- La IA no escribe documentos clinicos finales sin confirmacion humana.
- Todo borrador expone fuentes, faltantes, certeza y auditoria.
- Todo borrador SOAP expone trazabilidad por seccion S/O/A/P.
- Ollama es opcional; Nivel 0 debe funcionar con reglas locales.
- Toda inteligencia debe tener representacion visual y accion humana.

## Contratos principales

- `POST /api/v1/patients/{patient_id}/ai/clinical-intent`
- `POST /api/v1/patients/{patient_id}/ai/clinical-intent-route`
- `POST /api/v1/patients/{patient_id}/ai/review-item-decision`
- `POST /api/v1/patients/{patient_id}/ai/draft-soap-from-events`

## Intenciones iniciales

- `summarize_patient`
- `daily_changes`
- `active_problems`
- `timeline`
- `draft_soap`
- `show_sources`

## Documentos relacionados

- Vision: `docs/AI_CHART_INTERACTION_VISION.md`
- Nivel 0: `docs/SIMULATED_CLINICAL_INTELLIGENCE.md`
- Fases: `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`
- UI visible: `docs/VISUAL_INTELLIGENCE_COUPLING.md`
