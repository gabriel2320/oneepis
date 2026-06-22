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
- Next Route Handlers pueden transmitir vistas previas de interaccion, pero no son autoridad clinica.
- El AI Bridge transmite eventos tipados: `status`, `source`, `warning`, `proposal`, `done`.
- Toda propuesta que pueda terminar en escritura debe expresarse como `ClinicalPatch` revisable.

## Contratos principales

- `POST /api/v1/patients/{patient_id}/ai/clinical-intent`
- `POST /api/v1/patients/{patient_id}/ai/clinical-intent-route`
- `POST /api/v1/patients/{patient_id}/ai/review-item-decision`
- `POST /api/v1/patients/{patient_id}/ai/draft-soap-from-events`
- `POST /api/v1/patients/{patient_id}/ai/event-proposals-from-entry`
- `POST /api/v1/patients/{patient_id}/ai/confirm-clinical-patch`

## ClinicalPatch

Las propuestas que pueden escribir ficha salen como `ClinicalPatch`:

```text
target -> clinical_event | evolution | problem | medication | document
mode -> draft | suggestion
operations -> add | replace | annotate
sources -> fuentes visibles
warnings -> limites clinicos
requires_human_confirmation -> true
```

Estado actual:

- v0 soporta `clinical_event` y `evolution`.
- Las evoluciones escritas generan propuestas de eventos con patch incluido.
- La UI muestra las operaciones principales del patch antes de confirmar.
- La UI muestra estado local de propuesta: `pendiente`, `registrando`, `registrada en ficha` o `rechazada`.
- Aceptar el patch crea un evento clinico auditado.
- Guardar SOAP generado usa `target=evolution` y crea solo borrador no firmado.
- Rechazar el patch audita la decision sin persistir cambios.
- La UI no arma escrituras desde campos sueltos; envia la decision al backend.

Siguiente mejora permitida:

- hacer mas claros los permisos bloqueados y cubrir el flujo con E2E, sin agregar nuevas rutas IA.

## AI Bridge

El bridge recomendado es:

```text
UI AI-Chart -> Next Route Handler -> FastAPI -> eventos tipados -> UI
```

Next puede mejorar experiencia y streaming. FastAPI conserva contexto clinico,
permisos, auditoria y persistencia. El bridge no debe multiplicarse en muchos
endpoints especializados hasta que exista un nucleo compartido.

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
