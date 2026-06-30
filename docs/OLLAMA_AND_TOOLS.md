# Ollama

## Objetivo

La IA local debe asistir documentacion clinica, no tomar decisiones autonomas.

Ollama es Nivel 1. OneEpis debe ser util antes de Ollama mediante `Simulated Clinical Intelligence`: reglas, plantillas, timeline, validadores, contexto y auditoria. Ver `docs/SIMULATED_CLINICAL_INTELLIGENCE.md`.

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
ONEEPIS_OLLAMA_MODEL_SUGGESTIONS=qwen3:8b
ONEEPIS_OLLAMA_MODEL_EMBEDDINGS=bge-m3
```

Uso recomendado:

- `llama3.2:latest`: fallback rapido y liviano para borradores simples.
- `qwen3:8b`: resumen y sugerencias clinicas conservadoras si latencia y VRAM son aceptables.
- `bge-m3`: embeddings futuros para busqueda/RAG, no usado en fase 1.

No cargar varios modelos grandes al mismo tiempo en 12 GB VRAM salvo pruebas controladas.

## API usada

La implementacion Ollama usa:

- `/api/tags` para disponibilidad local de modelos.
- `/api/chat` con `stream=false` y `format=json`.

Superficies actuales de IA:

- `GET /api/v1/ai/status`: estado Ollama y modelos por tarea.
- `POST /api/v1/ai/clinical-insights`: borrador desde texto clinico.
- `POST /api/v1/patients/{patient_id}/ai/suggestions`: sugerencias temporales desde snapshot.

Ninguna superficie IA persiste, firma ni modifica ficha.

## Modo sin Ollama

Si Ollama esta apagado o lento, el sistema debe seguir funcionando con:

- resumen por plantilla
- contexto clinico desde eventos
- comparacion minima con evolucion previa
- borrador SOAP estructurado
- faltantes y marcas de evidencia
- fuentes y auditoria

La UI debe comunicarlo como degradacion controlada, no como falla total del producto.

Referencias oficiales:

- https://docs.ollama.com/api/introduction
- https://docs.ollama.com/api/tags
- https://docs.ollama.com/api/chat
- https://ollama.com/library/llama3.2
- https://ollama.com/library/qwen3

## Fuera de fase 1

- uploads reales de documentos
- recetas firmadas
- soporte multiusuario clinico
- integraciones HL7/FHIR
- embeddings en produccion
- API externa con datos clinicos identificados

## Siguientes herramientas IA

- Privacy & Safety Gateway antes de IA externa.
- RAG gobernado solo despues de permisos, corpus aprobado y trazabilidad de fuente.
- Embeddings solo cuando exista un flujo documental auditado.

## IA externa

La IA externa sigue bloqueada. El contrato ejecutable vive en
`apps/api/src/oneepis_api/core/external_ai_contract.py`.

Antes de habilitar cualquier proveedor externo se requiere:

- gateway de privacidad PHI;
- desidentificacion o minimizacion por caso de uso;
- allowlist de proveedores aprobados;
- opt-in humano explicito;
- auditoria por solicitud externa;
- revision legal, seguridad y gobernanza clinica.
