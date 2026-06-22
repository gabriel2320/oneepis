# AI-Chart Interaction Vision

## Decision

AI-Chart no es un chatbot ni un asistente de formularios.

La interaccion objetivo es:

```text
IA, este paciente esta a mi cargo. Ordename el caso, muestrame lo importante,
prepara la ficha y dejame confirmar.
```

Regla central:

```text
la IA propone -> el humano confirma -> PostgreSQL registra -> auditoria explica
```

## Alcance

Este documento es vision de producto, no backlog. La ejecucion vive en
`docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`; el contrato conceptual vive en
`docs/AI_CHART_CORE.md`; la regla visual vive en
`docs/VISUAL_INTELLIGENCE_COUPLING.md`.

## Modos

- Lectura: resume, compara, ordena y muestra fuentes. No escribe ficha.
- Borrador: prepara texto editable. No firma ni consolida como dato final.
- Propuesta estructurada: crea items aceptables/rechazables uno a uno.
- Confirmacion humana: unica etapa que escribe en la fuente de verdad.

## Forma obligatoria de respuesta

Toda respuesta clinica debe exponer:

1. respuesta clinica
2. fuentes usadas
3. certeza o limite
4. datos faltantes
5. accion propuesta
6. confirmacion humana si escribe ficha

## Comandos iniciales permitidos

El MVP debe quedarse en comandos que puedan resolverse con contexto,
plantillas, reglas y auditoria:

- resume paciente
- que cambio desde ayer
- lista problemas activos
- crea timeline
- prepara evolucion S/O/A/P
- muestra fuentes
- guarda borrador con auditoria

No ampliar a medicamentos avanzados, documentos, alta, RAG o IA externa sin
pasar por `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`.
