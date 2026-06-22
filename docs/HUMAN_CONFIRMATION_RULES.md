# Human Confirmation Rules

OneEpis puede asistir, resumir y redactar, pero no puede cerrar actos clinicos por si solo.

## Reglas no negociables

- Un output IA siempre es borrador.
- Un borrador IA debe indicar `requires_human_confirmation=true`.
- El usuario humano debe editar o confirmar antes de guardar como documento clinico.
- La auditoria debe registrar proveedor, fuentes usadas y actor humano.
- Si Ollama esta apagado, la degradacion local debe ser explicita para el usuario.

## Aplicacion actual

`draft-soap-from-events` devuelve un borrador SOAP con:

- fuentes `clinical_event_id`
- proveedor
- disponibilidad IA
- advertencias
- confirmacion humana obligatoria

El endpoint no crea evoluciones. La UI guarda una evolucion solo cuando el usuario presiona guardar.
Antes de guardar el borrador generado, la UI exige una marca explicita de
revision humana en el margen inteligente. El borrador guardado registra en
`extra_data`:

- `requires_human_confirmation=true`
- `human_reviewed=true`
- `human_reviewed_at`
- fuentes y trazabilidad S/O/A/P usadas por AI-Chart

`clinical-intent` tampoco escribe ficha. Si la intencion produce borrador,
devuelve `requires_human_confirmation=true` y acciones propuestas que la UI debe
presentar como confirmacion explicita.

Los endpoints completos viven en `docs/AI_CHART_CORE.md`.
