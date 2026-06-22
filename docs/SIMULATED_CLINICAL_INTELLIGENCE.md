# Simulated Clinical Intelligence

## Decision

OneEpis debe ser util aunque Ollama este apagado.

La secuencia de inteligencia es:

```text
Nivel 0: reglas, plantillas, eventos, timeline, validadores y auditoria
Nivel 1: Ollama local como mejora de lenguaje/extraccion
Nivel 2: API externa opcional, anonimizada y auditada
```

Nivel 0 no es IA falsa. Es conducta clinica deterministica, visible y
auditable.

## Arquitectura

```text
ClinicalChatUI
  -> ClinicalIntentRouter
  -> ClinicalContextBuilder
  -> ClinicalRuleEngine
  -> ClinicalTemplateEngine
  -> ClinicalDraftBuilder
  -> HumanConfirmationService
  -> AuditLog
```

Ollama y API externa son capas superiores, no requisitos para operar.

## Capacidades Nivel 0

Estas capacidades pueden y deben partir sin LLM:

- resumen de paciente desde datos estructurados
- comparacion 24 h
- evolucion S/O/A/P basica
- faltantes clinicos
- timeline
- fuentes visibles
- propuestas aceptables/rechazables
- preferencias confirmadas, cuando existan

## Limites

No simular razonamiento que requiera lenguaje libre complejo:

- PDF clinico desordenado
- reconciliacion farmacologica avanzada
- resumen documental largo
- epicrisis narrativa avanzada
- RAG

Esos frentes requieren fases posteriores del plan progresivo.

## Relacion con AI-Chart Core

AI-Chart ya implementa parte del Nivel 0:

- `clinical_events`
- `clinical-intent`
- router deterministico
- reglas 24 h
- `review_items`
- fuentes y faltantes
- hoja SOAP con margen inteligente
- auditoria de decisiones

El backlog unico vive en `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`.
