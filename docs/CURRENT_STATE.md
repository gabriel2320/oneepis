# Current State

## Fase 1 cerrada, PR #1 mergeado, Fase 2 gobernada

OneEpis ya tiene una base E2E real:

1. Crear paciente en UI.
2. Abrir ficha.
3. Crear evolucion SOAP.
4. Persistir en PostgreSQL via FastAPI.
5. Registrar auditoria por escritura.
6. Refrescar UI con React Query.

El modo demo solo debe usarse con `NEXT_PUBLIC_DEMO_MODE=true`.

PR #1 (`[codex] Close AI-Chart phase 1`) fue revisado como cambio de riesgo,
endurecido y mergeado por squash en `main` el 2026-06-23.

Programa de lectura aprobado, no implementado: `PROG-ASSISTANT-READ-01`.

Este programa define una capa futura de asistente clinico de solo lectura para
leer, buscar, mostrar, graficar y correlacionar la historia longitudinal del
paciente. Queda integrado en `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md` como
extension cerrada de Fase 2 y gobernado por `docs/GOVERNANCE.md`.

Estado real al 2026-06-23:

- no existen todavia endpoints `/assistant/*`
- no existe todavia ruta `/pacientes/[patientId]/contexto`
- no hay busqueda, chart ni correlacion assistant dedicados
- no se autoriza escritura clinica desde el programa
- `ClinicalPatch` v0 soporta escritura confirmada solo para `clinical_event` y `evolution`
- el backend bloquea aceptar patches con `requires_human_confirmation=false`
- el backend bloquea guardar evoluciones AI-Chart que no queden en `status=draft`
- la UI de propuestas desde evolucion exige permiso AI para confirmar patches
- el siguiente bloque debe partir desde `main` verde y ser micro-PR logico

## Backend

Router principal: `apps/api/src/oneepis_api/api/v1/routes/patients.py`.

Dominios CRUD:

- pacientes
- encuentros clinicos
- clinical entries con vinculo opcional a encuentro
- clinical events como hechos longitudinales
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

Higiene local:

- en `development`, la API rechaza escrituras de paciente con terminos de fixtures externos conocidos
- esta guardia evita recontaminar PostgreSQL local con datos de proyectos previos
- no reemplaza permisos, auditoria ni limpieza manual de bases ya contaminadas

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
- `POST /api/v1/patients/{patient_id}/ai/clinical-intent`
- `POST /api/v1/patients/{patient_id}/ai/clinical-intent-route`
- `POST /api/v1/patients/{patient_id}/ai/review-item-decision`
- `POST /api/v1/patients/{patient_id}/ai/draft-soap-from-events`
- `POST /api/v1/patients/{patient_id}/ai/event-proposals-from-entry`
- `POST /api/v1/patients/{patient_id}/ai/confirm-clinical-patch`
- factory compatible en `services/ai/provider.py`
- contrato, providers, parsing y sugerencias snapshot separados en `services/ai/*`
- Ollama es first-class en desarrollo, con fallback no bloqueante
- AI-Chart Core funciona como Nivel 0: reglas, plantillas, fuentes, faltantes, review items auditados, hoja SOAP con margen inteligente, propuestas de eventos desde evoluciones escritas y guardado por `ClinicalPatch` confirmado aunque Ollama este apagado
- las aceptaciones `ClinicalPatch` quedan limitadas por contrato: confirmacion humana obligatoria, evolucion siempre borrador no firmado y auditoria de bloqueo cuando no aplica

Hospitalizacion:

- `GET /api/v1/hospitalization/active`
- `GET/POST/PATCH /api/v1/hospitalization/beds`
- `GET/POST/PATCH /api/v1/hospitalization/patients/{patient_id}/daily-sheets`
- `GET/POST/PATCH /api/v1/hospitalization/patients/{patient_id}/indications`
- tablero `/hospitalizacion/camas` lee encuentros `hospitalization` en curso
- camas estructuradas con sala/habitacion/cama y asignacion auditada a encuentros activos
- UI `/hospitalizacion/camas` administra estados y `/hospitalizacion/camas/nueva` crea camas
- camas disponibles pueden asignarse a ingresos activos sin cama; una cama ocupada debe liberarse antes de reasignarse
- hoja diaria hospitalizada tiene PostgreSQL, API, permisos, auditoria, OpenAPI, crear/listar/editar/cerrar UI y print
- estado de hoja diaria: `draft` o `closed`; `closed` bloquea edicion posterior sin equivaler a firma legal
- fecha de hoja diaria: debe estar dentro de la ventana del ingreso hospitalario asociado usando fecha clinica local `America/Santiago`, no el dia UTC crudo
- `/hospitalizacion/rondas` es vista de lectura: ingresos activos, cama, ultima hoja diaria y accesos a ficha/papel
- `/print/hospitalizacion/rondas` imprime ronda de lectura con ingresos activos, cama y ultima hoja diaria
- indicacion hospitalaria minima tiene PostgreSQL, API, permisos, auditoria, OpenAPI, UI y papel
- estado de indicacion hospitalaria: `draft` o `closed`; `closed` bloquea edicion posterior sin equivaler a firma legal
- receta ya tiene politica de gobierno en `docs/GOVERNANCE.md`, pero aun no tiene modelo, endpoint ni firma real
- aun no existen indicaciones firmadas, recetas validas ni rondas con escritura clinica propia

Consulta:

- `/consulta/pacientes/{patient_id}/atencion` usa endpoints existentes para crear encuentro ambulatorio y evolucion SOAP vinculada
- no hay agenda productiva todavia; `/consulta/agenda` sigue como borde preparado
- resumen ambulatorio dedicado sigue preparado; la ficha paciente continua siendo el centro longitudinal

## Frontend

Rutas App Router bajo `apps/web/src/app`.

Capas:

- `src/app/api/ai/clinical-command/route.ts`: BFF streaming con Vercel AI SDK; orquesta FastAPI y no reemplaza la API clinica canonica
- `src/lib/api/*`: clientes API por dominio
- `src/lib/api/auth.ts`: login local y sesion actual
- `src/lib/types.ts`: contrato TypeScript
- `src/components/auth/*`: login local y badge de sesion
- `src/components/layout/app-shell.tsx`: navegacion global
- temas visuales usan tokens de superficie (`surface`, `surface-subtle`, `surface-raised`) y selector con swatch
- `src/components/clinical/patient-clinical-shell.tsx`: mesa clinica por paciente
- `src/components/clinical/patient-*-pages.tsx`: pantallas paciente importadas directo por App Router
- `/pacientes` funciona como mesa clinica de entrada con buscador, metricas operativas y lista escaneable
- `/pacientes/[patientId]/eventos` registra hechos clinicos longitudinales
- `/pacientes/[patientId]/ai-chart` muestra inteligencia simulada, intenciones clinicas, propuestas revisables y hoja SOAP editable con margen inteligente
- AI-Chart envia la barra clinica al BFF de Next, que delega la resolucion estructurada en FastAPI y transmite eventos tipados JSONL con AI SDK
- AI-Chart no guarda propuestas desde campos sueltos; envia `ClinicalPatch` al backend para aceptar/rechazar/guardar
- AI-Chart muestra estado operativo de eventos, evoluciones, seleccion, modo y permisos antes de generar o guardar
- AI-Chart explica acciones bloqueadas con condicion o rol habilitante
- AI-Chart inicia Context Builder serio mostrando explicaciones por problema: por que una evidencia se asocia o queda sin vinculo
- AI-Chart muestra faltantes con razon y contexto asistencial, no solo nombres de datos ausentes
- AI-Chart agrupa reglas narrativas de mejoria/empeoramiento como `Curso clinico`
- AI-Chart etiqueta el curso clinico por dominio cuando el texto reciente permite distinguir respiratorio, dolor, infeccioso, hemodinamico, metabolico o digestivo
- AI-Chart evita negaciones obvias de curso clinico y corrobora dominios respiratorio, infeccioso o hemodinamico con signos vitales cuando existen dos controles comparables
- AI-Chart asocia problemas con eventos por vocabulario clinico local explicable cuando no hay coincidencia literal
- AI-Chart evita negaciones obvias al asociar por vocabulario local para reducir falsos positivos
- AI-Chart prioriza asociaciones SNOMED CT cuando el problema trae codigo y el evento incluye conceptos/ancestros derivados de repositorios terminologicos externos licenciados
- AI-Chart agrega pendientes por problema activo segun dominio clinico probable: respiratorio, metabolico, hemodinamico, infeccioso o renal
- AI-Chart muestra razon de asociacion y fuente abreviada por cada evidencia vinculada a problema
- AI-Chart vuelve a mantener `patient-ai-chart-pages.tsx` bajo presupuesto como orquestador; el flujo de propuestas desde evolucion vive en su seccion propia
- Propuestas desde evolucion muestran estado visible `pendiente`, `registrando`, `registrada en ficha` o `rechazada` antes y despues de confirmar el `ClinicalPatch`
- Las decisiones de propuesta se consideran durables via auditoria; la UI mantiene estado local de sesion para operacion inmediata
- La vista de operaciones `ClinicalPatch` esta extraida como componente reusable para evitar inflar paneles AI-Chart
- `src/components/clinical/ambulatory-visit-pages.tsx`: atencion ambulatoria minima sobre encuentros y SOAP
- `src/components/clinical/*`: cards, widgets y pantallas clinicas
- `src/components/print/*`: hojas imprimibles
- las rutas print no hacen fallback silencioso a otro documento cuando el ID solicitado no existe

Tests API:

- fixtures compartidas en `apps/api/tests/conftest.py`
- cobertura paciente separada por dominios: ficha, permisos, auditoria, IA y encuentros
- cobertura hospitalizacion separada por board, camas y hoja diaria
- `ClinicalPatch` cubre aceptacion, rechazo, target no soportado, bloqueo por falta de confirmacion humana y bloqueo de evolucion no borrador; targets fuera de alcance no escriben ficha y quedan auditados como `ai.clinical_patch.unsupported` o `ai.clinical_patch.blocked`

Deuda visible a resolver antes de nuevo crecimiento clinico:

- no agregar nueva clinica core sin flujo completo PostgreSQL/API/permisos/auditoria/OpenAPI/UI
- sostener `/pacientes` como mesa clinica de entrada, no como dashboard ni portada generica
- `apps/web/src/components/print/clinical-print.tsx` esta cerca del presupuesto de complejidad; no inflarlo con mas papel sin separar.
- `apps/web/src/lib/types.ts` supera 300 lineas por ser contrato manual compartido; vigilar antes de sumar muchos dominios.
- `apps/web/src/components/clinical/ai-chart/*` concentra subcomponentes AI-Chart; mantener `patient-ai-chart-pages.tsx` como orquestador y no volver a inflarlo.
- tras R-01, cualquier crecimiento AI-Chart debe entrar en componentes existentes o extraer subpaneles; no agregar bloques inline grandes a la pagina.
- `apps/api/src/oneepis_api/services/clinical_intent.py` ya concentra reglas deterministicas; nuevas reglas deben agruparse por dominio o extraerse antes de crecer mucho mas.
- `apps/api/src/oneepis_api/services/clinical_patch.py` concentra aplicacion y auditoria de patches aceptados/rechazados.
- `apps/api/src/oneepis_api/api/v1/routes/patient_events.py` sigue agrupando eventos e intenciones; no refactorizar mas sin otra familia de rutas IA.
- `/consulta/agenda`, `/consulta/pacientes/[patientId]/resumen`, documentos y receta siguen como bordes preparados; no expandir todos a la vez.
- receta impresa sigue bloqueada hasta tener firma, folio, actor, fecha clinica y permisos claros.
- rondas lee hojas diarias por paciente activo; aceptable por ahora, pero requerira read-model backend si escala.

## Auditoria rapida 2026-06-23

- Ultimos bloques completados: hoja diaria, cierre, reglas de fecha, rondas de lectura, fecha clinica local, politica de indicaciones/receta, indicacion minima, atencion ambulatoria minima, mesa `/pacientes` v2, temas visuales v2, AI-Chart Core Nivel 0, PR #1 mergeado y endurecimiento `ClinicalPatch`.
- Se detecto contaminacion local de datos desde fixtures externos en PostgreSQL de desarrollo; la base local fue limpiada y el nuevo foco es blindar identidad/datos antes de crecer.
- Validacion reciente local post-merge: ruff API, 66 tests API, web typecheck/lint/build, OpenAPI sin diff contractual y Playwright e2e 27 passed / 1 skipped.
- Validacion remota PR #1: `api`, `web` y `contracts-e2e` verdes antes del squash merge.
- Siguiente paso recomendado: abrir `PROG-ASSISTANT-READ-01` como capa de lectura clinica, no como chat, RAG, dashboard ni escritura.
- Siguiente bloque de producto despues de Assistant Read: diseno de examenes/laboratorio estructurados con entidad dedicada, manteniendo compatibilidad de `clinical_events.exam_result`.

## Historial

El historial cronologico vive en `docs/ROADMAP.md`.
La guia operativa para agentes vive en `docs/CODEX_PLAN.md`.

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
