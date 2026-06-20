# Current State

## Fase 1 implementada

OneEpis ya tiene una base E2E real:

1. Crear paciente en UI.
2. Abrir ficha.
3. Crear evolucion SOAP.
4. Persistir en PostgreSQL via FastAPI.
5. Registrar auditoria por escritura.
6. Refrescar UI con React Query.

El modo demo solo debe usarse con `NEXT_PUBLIC_DEMO_MODE=true`.

## Backend

Router principal: `apps/api/src/oneepis_api/api/v1/routes/patients.py`.

Dominios CRUD:

- pacientes
- clinical entries
- alergias
- medicacion
- signos vitales

Auditoria:

- cada escritura usa `record_audit_event`
- actor via `X-OneEpis-Actor`
- fallback: `dev.system`
- lectura: `GET /api/v1/patients/{patient_id}/audit-events`

IA:

- `GET /api/v1/ai/status`
- `POST /api/v1/ai/clinical-insights`
- `POST /api/v1/patients/{patient_id}/ai/suggestions`
- provider desacoplado en `services/ai/provider.py`
- Ollama es first-class en desarrollo, con fallback no bloqueante

## Frontend

Rutas App Router bajo `apps/web/src/app`.

Capas:

- `src/lib/api/*`: clientes API por dominio
- `src/lib/types.ts`: contrato TypeScript
- `src/components/layout/app-shell.tsx`: navegacion global
- `src/components/clinical/patient-clinical-shell.tsx`: mesa clinica por paciente
- `src/components/clinical/*`: cards, widgets y pantallas clinicas
- `src/components/print/*`: hojas imprimibles

## Programa activo PR-018 a PR-025

- PR-018: Ollama first-class local.
- PR-019: IA acoplada a ficha paciente.
- PR-020: Patient Clinical Shell.
- PR-021: Ficha resumen tipo mesa clinica.
- PR-022: Una accion = una pantalla.
- PR-023: SOAP con asistente Ollama.
- PR-024: Modo papel v2.
- PR-025: QA visual + Ollama.

Regla IA: todo output de Ollama es borrador, requiere revision humana y no escribe ficha automaticamente.

## Gates actuales

Comandos esperados antes de entregar cambios:

```bash
.venv/Scripts/python -m ruff check apps/api
.venv/Scripts/python -m pytest apps/api/tests
npm --workspace apps/web run typecheck
npm --workspace apps/web run lint
npm --workspace apps/web run build
python apps/api/scripts/export_openapi.py
```
