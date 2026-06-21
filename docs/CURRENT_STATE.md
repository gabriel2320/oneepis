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
- encuentros clinicos
- clinical entries con vinculo opcional a encuentro
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
- fuera de `development`, la API rechaza secreto default, usuarios default, actor dev y auth desactivada

Permisos finos:

- matriz viva en `docs/PERMISSIONS.md`
- enfermeria puede registrar signos vitales, pero no SOAP, medicacion, alergias ni IA clinica
- encuentros clinicos requieren rol medico/admin/dev
- problemas activos requieren rol medico/admin/dev
- estado de ficha y contexto asistencial se editan desde UI con rol medico/admin/dev
- solo_lectura puede leer, pero no escribir
- frontend deshabilita acciones sin permiso; backend las rechaza con 403

IA:

- `GET /api/v1/ai/status`
- `POST /api/v1/ai/clinical-insights`
- `POST /api/v1/patients/{patient_id}/ai/suggestions`
- factory compatible en `services/ai/provider.py`
- contrato, providers, parsing y sugerencias snapshot separados en `services/ai/*`
- Ollama es first-class en desarrollo, con fallback no bloqueante

Hospitalizacion:

- `GET /api/v1/hospitalization/active`
- `GET/POST/PATCH /api/v1/hospitalization/beds`
- tablero `/hospitalizacion/camas` lee encuentros `hospitalization` en curso
- camas estructuradas con sala/habitacion/cama y asignacion auditada a encuentros activos
- UI `/hospitalizacion/camas` administra estados y `/hospitalizacion/camas/nueva` crea camas
- camas disponibles pueden asignarse a ingresos activos sin cama; una cama ocupada debe liberarse antes de reasignarse
- aun no existen indicaciones ni rondas auditadas

## Frontend

Rutas App Router bajo `apps/web/src/app`.

Capas:

- `src/lib/api/*`: clientes API por dominio
- `src/lib/api/auth.ts`: login local y sesion actual
- `src/lib/types.ts`: contrato TypeScript
- `src/components/auth/*`: login local y badge de sesion
- `src/components/layout/app-shell.tsx`: navegacion global
- `src/components/clinical/patient-clinical-shell.tsx`: mesa clinica por paciente
- `src/components/clinical/patient-*-pages.tsx`: pantallas paciente importadas directo por App Router
- `src/components/clinical/*`: cards, widgets y pantallas clinicas
- `src/components/print/*`: hojas imprimibles

Tests API:

- fixtures compartidas en `apps/api/tests/conftest.py`
- cobertura paciente separada por dominios: ficha, permisos, auditoria, IA, encuentros y hospitalizacion

Deuda visible a resolver antes de nuevo crecimiento clinico:

- no agregar nueva clinica core sin flujo completo PostgreSQL/API/permisos/auditoria/OpenAPI/UI

## Programa activo PR-018 a PR-052

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
- PR-030: Pantalla gobernada para editar estado clinico y contexto asistencial.
- PR-031: Encuentros clinicos auditados como puente para consulta y hospitalizacion.
- PR-032: Evoluciones SOAP vinculables a encuentros clinicos.
- PR-033: Tablero hospitalario simple desde encuentros de hospitalizacion activos.
- PR-034: Camas hospitalarias estructuradas con asignacion auditada.
- PR-035: Administracion UI de camas y creacion dedicada.
- PR-036: Asignacion de ingresos activos a camas existentes.
- PR-037: CI real con ruff, lint, build, OpenAPI y Playwright.
- PR-038: Seguridad fail-closed fuera de development.
- PR-039: Dieta inicial de `patient-pages.tsx` con barrel compatible.
- PR-040: Playwright inicia servidor fresco por defecto; reuse solo con `PLAYWRIGHT_REUSE_SERVER=true`.
- PR-041: Doctrina anti-inflacion canonica en `docs/GOVERNANCE.md`.
- PR-042: Gates oficiales como pocos comandos raiz.
- PR-043: Dieta backend de pacientes sin cambiar OpenAPI.
- PR-044: Retiro del barrel temporal frontend de paciente.
- PR-045: Papel serio con smoke print dedicado.
- PR-046: Criterio para proximo crecimiento clinico minimo.
- PR-047: Alinear guias y gates oficiales.
- PR-048: Retiro de legacy demo frontend.
- PR-049: Dieta UI sin cambiar conducta.
- PR-050: Dieta IA backend.
- PR-051: Dieta tests API.
- PR-052: Elegir crecimiento clinico minimo, recomendado hoja diaria hospitalizada.

Regla IA: todo output de Ollama es borrador, requiere revision humana y no escribe ficha automaticamente.

## Gates actuales

Comandos esperados antes de entregar cambios:

```bash
npm run check:api
npm run check:web
npm run check:contract
npm run check:e2e
npm run check
```
