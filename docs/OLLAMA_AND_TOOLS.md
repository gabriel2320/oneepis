# Ollama and Tools

## Objetivo

La IA local debe asistir documentacion clinica, no tomar decisiones autonomas.

Reglas:

- no diagnosticar
- no firmar
- no indicar tratamientos nuevos
- no escribir ficha sin confirmacion humana
- no enviar datos clinicos a terceros

## Modelos para RTX 5070 12 GB

Variables:

```bash
ONEEPIS_AI_PROVIDER=ollama
ONEEPIS_OLLAMA_BASE_URL=http://localhost:11434
ONEEPIS_OLLAMA_MODEL=llama3.2:latest
ONEEPIS_OLLAMA_MODEL_SUMMARY=qwen3:8b
ONEEPIS_OLLAMA_MODEL_EMBEDDINGS=bge-m3
```

Uso recomendado:

- `llama3.2:latest`: fallback rapido y liviano para borradores simples.
- `qwen3:8b`: resumen/razonamiento clinico conservador si latencia y VRAM son aceptables.
- `bge-m3`: embeddings futuros para busqueda/RAG, no usado en fase 1.

No cargar varios modelos grandes al mismo tiempo en 12 GB VRAM salvo pruebas controladas.

## API usada

El provider actual usa:

- `/api/tags` para disponibilidad local de modelos.
- `/api/chat` con `stream=false` y `format=json`.

Referencias oficiales:

- https://docs.ollama.com/api/introduction
- https://docs.ollama.com/api/tags
- https://docs.ollama.com/api/chat
- https://ollama.com/library/llama3.2
- https://ollama.com/library/qwen3

## Herramientas recomendadas para fases siguientes

- Auth y permisos: antes de uploads, recetas, firma o auditoria legal.
- Politica PHI: clasificacion de datos, logs, backups, retencion y borrado.
- RAG gobernado: solo despues de permisos, corpus aprobado y trazabilidad de fuente.
- Playwright: cobertura visual de rutas principales y print.
- OpenAPI codegen: generar tipos cliente cuando el contrato se estabilice.
- Sentry/OpenTelemetry: observabilidad sin PHI en logs.
- Alembic discipline: cada cambio de modelo debe tener migracion y prueba.

## Fuera de fase 1

- uploads reales de documentos
- recetas firmadas
- soporte multiusuario clinico
- integraciones HL7/FHIR
- embeddings en produccion
