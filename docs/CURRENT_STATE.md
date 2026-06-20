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
- problemas activos
- alergias
- medicacion
- signos vitales

Auditoria:

- cada escritura usa `record_audit_event`
- actor via token local de `/api/v1/auth/login`
- `X-OneEpis-Actor` queda solo como fallback dev si `ONEEPIS_AUTH_ALLOW_DEV_ACTOR_HEADER=true`
- lectura: `GET /api/v1/patients/{patient_id}/audit-events`
- cada request recibe `correlation_id` y se expone en `X-OneEpis-Correlation-ID`
- eventos guardan `request_method`, `request_path` y snapshots `before/after` cuando aplica
- detalle operativo en `docs/AUDIT.md`

Auth local:

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- roles iniciales: `admin`, `medico`, `enfermeria`, `solo_lectura`, `dev`
- rutas de paciente requieren autenticacion
- escrituras clinicas requieren `admin`, `medico`, `enfermeria` o `dev`
- IA clinica requiere `admin`, `medico` o `dev`

Permisos finos:

- matriz viva en `docs/PERMISSIONS.md`
- enfermeria puede registrar signos vitales, pero no SOAP, medicacion, alergias ni IA clinica
- problemas activos requieren rol medico/admin/dev
- solo_lectura puede leer, pero no escribir
- frontend deshabilita acciones sin permiso; backend las rechaza con 403

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
- `src/lib/api/auth.ts`: login local y sesion actual
- `src/lib/types.ts`: contrato TypeScript
- `src/components/auth/*`: login local y badge de sesion
- `src/components/layout/app-shell.tsx`: navegacion global
- `src/components/clinical/patient-clinical-shell.tsx`: mesa clinica por paciente
- `src/components/clinical/*`: cards, widgets y pantallas clinicas
- `src/components/print/*`: hojas imprimibles

## Programa activo PR-018 a PR-029

- PR-018: Ollama first-class local.
- PR-019: IA acoplada a ficha paciente.
- PR-020: Patient Clinical Shell.
- PR-021: Ficha resumen tipo mesa clinica.
- PR-022: Una accion = una pantalla.
- PR-023: SOAP con asistente Ollama.
- PR-024: Modo papel v2.
- PR-025: QA visual + Ollama.
- PR-026: Auth local + roles + actor auditado.
- PR-027: Permisos clinicos por accion.
- PR-028: Auditoria fuerte con correlation ID y before/after.
- PR-029: Estado de ficha, contexto asistencial y problemas activos auditados.

Regla IA: todo output de Ollama es borrador, requiere revision humana y no escribe ficha automaticamente.

## Gates actuales

Comandos esperados antes de entregar cambios:

```bash
.venv/Scripts/python -m ruff check apps/api
.venv/Scripts/python -m pytest apps/api/tests
npm --workspace apps/web run typecheck
npm --workspace apps/web run lint
npm --workspace apps/web run build
.venv/Scripts/python apps/api/scripts/export_openapi.py
```
