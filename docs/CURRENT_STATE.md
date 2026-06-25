# Current State

## Fase 1 cerrada, Fase 2 iniciada

OneEpis ya tiene una base E2E real:

1. Crear paciente en UI.
2. Abrir ficha.
3. Crear evolucion SOAP.
4. Persistir en PostgreSQL via FastAPI.
5. Registrar auditoria por escritura.
6. Refrescar UI con React Query.

El modo demo solo debe usarse con `NEXT_PUBLIC_DEMO_MODE=true`.

Programa de lectura iniciado: `PROG-ASSISTANT-READ-01`.

Este programa define una capa de asistente clinico de solo lectura para
leer, buscar, mostrar, graficar y correlacionar la historia longitudinal del
paciente. Queda integrado en `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md` como
extension cerrada de Fase 2 y gobernado por `docs/GOVERNANCE.md`.

Estado real al 2026-06-25:

- existe `GET /api/v1/patients/{patient_id}/assistant/timeline`
- existe `POST /api/v1/patients/{patient_id}/assistant/search`
- existe `POST /api/v1/patients/{patient_id}/assistant/chart`
- existe `POST /api/v1/patients/{patient_id}/assistant/correlate`
- no existe todavia ruta `/pacientes/[patientId]/contexto`
- no se autoriza escritura clinica desde el programa
- el asistente de lectura es deterministico, declara fuentes/faltantes/limites y no registra auditoria de modificacion

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

Asistente de lectura:

- `GET /api/v1/patients/{patient_id}/assistant/timeline`
- `POST /api/v1/patients/{patient_id}/assistant/search`
- `POST /api/v1/patients/{patient_id}/assistant/chart`
- `POST /api/v1/patients/{patient_id}/assistant/correlate`
- une encuentros, evoluciones, eventos, signos vitales, problemas activos,
  medicacion activa, alergias activas e indicaciones hospitalarias existentes
- responde con `source_type`, `source_id`, fecha disponible, resumen, estado,
  detalles, faltantes y limites
- busca texto deterministico sobre fuentes normalizadas, sin embeddings, RAG ni
  IA generativa
- devuelve series graficables de signos vitales, eventos `exam_result` y marcas
  temporales de medicacion activa, sin acoplar imagenes ni componentes UI al backend
- correlaciona fuentes con presets cerrados `fever_infection`,
  `renal_medications`, `respiratory_oxygen`, `hemoglobin_bleeding` y
  `medication_changes`, sin diagnosticar ni prescribir
- es solo lectura: no crea, actualiza ni elimina datos clinicos, y no registra
  eventos de auditoria de modificacion

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
- `screen-capabilities.ts` separa `lifecycle` tecnico de `clinicalUse`;
  `complete` no implica uso clinico real, firma legal, receta valida ni orden
  ejecutable

Tests API:

- fixtures compartidas en `apps/api/tests/conftest.py`
- cobertura paciente separada por dominios: ficha, permisos, auditoria, IA y encuentros
- cobertura hospitalizacion separada por board, camas y hoja diaria
- `ClinicalPatch` cubre aceptacion, rechazo y target no soportado; targets fuera de alcance no escriben ficha y quedan auditados como `ai.clinical_patch.unsupported`

Deuda visible a resolver antes de nuevo crecimiento clinico:

- no agregar nueva clinica core sin flujo completo PostgreSQL/API/permisos/auditoria/OpenAPI/UI
- sostener `/pacientes` como mesa clinica de entrada, no como dashboard ni portada generica
- `apps/web/src/components/print/clinical-print.tsx` esta cerca del presupuesto de complejidad; no inflarlo con mas papel sin separar.
- `apps/web/src/lib/types.ts` supera 300 lineas por ser contrato manual compartido; vigilar antes de sumar muchos dominios.
- `apps/web/src/components/clinical/ai-chart/*` concentra subcomponentes AI-Chart; mantener `patient-ai-chart-pages.tsx` como orquestador y no volver a inflarlo.
- tras R-01, cualquier crecimiento AI-Chart debe entrar en componentes existentes o extraer subpaneles; no agregar bloques inline grandes a la pagina.
- `apps/api/src/oneepis_api/services/clinical_intent.py` queda como orquestador de intenciones; las reglas de cambios deterministicas viven en `clinical_intent_rules.py`.
- Los servicios assistant de lectura quedan separados por capacidad:
  `assistant_timeline.py`, `assistant_search.py`, `assistant_chart.py` y
  `assistant_correlations.py`; no agregar nuevas capacidades ahi sin extraer por
  dominio.
- `apps/api/src/oneepis_api/services/clinical_patch.py` concentra aplicacion y auditoria de patches aceptados/rechazados.
- `apps/api/src/oneepis_api/api/v1/routes/patient_events.py` sigue agrupando eventos e intenciones; no refactorizar mas sin otra familia de rutas IA.
- `/consulta/agenda`, `/consulta/pacientes/[patientId]/resumen`, documentos y receta siguen como bordes preparados; no expandir todos a la vez.
- receta impresa sigue bloqueada hasta tener firma, folio, actor, fecha clinica y permisos claros.
- rondas lee hojas diarias por paciente activo; aceptable por ahora, pero requerira read-model backend si escala.

## Auditoria clinica rapida 2026-06-24

Veredicto operativo: OneEpis es un scaffold clinico avanzado y gobernado, no una
ficha medica productiva. La direccion es correcta porque mantiene PostgreSQL
como verdad clinica, FastAPI como frontera, OpenAPI como contrato, Next.js como
proyeccion, papel como vista documental, auditoria como memoria e IA como ayuda
limitada.

Fortalezas actuales:

- flujo paciente -> ficha -> SOAP -> PostgreSQL -> auditoria -> React Query ya existe
- permisos por rol y rechazos 403 estan cubiertos por gate ejecutable
- pantallas, papel, contratos frontend y trazabilidad tienen reportes/gates propios
- auditoria de lectura ya tiene inventario report-only en `reports/read-access-map.*`
- politica futura de auditoria de lectura esta propuesta en
  `reports/read-access-policy.*`, con candidatos report-only de volumen y
  retencion
- ficha paciente formal v0.5 tiene caratula compacta con problemas, alergias y
  medicacion, mas antecedentes estructurados
  basados en `PatientRecordSnapshot`, con identificacion/contexto y paridad
  basica en papel de ficha sin duplicar fuente primaria
- eje de episodio esta auditado en `reports/encounter-axis-map.*` sin migraciones nuevas
- `npm run check:architecture` agrupa `check:screens`, `check:permissions`,
  `check:paper`, `check:contracts:drift`, `check:traceability` y la politica
  report-only de auditoria de lectura
- `npm run check` incluye API, web, contrato, arquitectura y E2E
- `check:screens` falla si una ruta bloqueada no declara `clinicalUse=blocked`
  o si un papel limitado se marca como `clinically-valid`

Validacion registrada:

- `npm run check:api`: 72 tests pasados, con una advertencia conocida de Starlette/httpx
- `npm run check:architecture`: verde con 0 brechas criticas en pantallas, permisos, papel, contratos y trazabilidad

Bloqueantes clinicos/productivos:

- no usar con datos reales de pacientes
- no existe todavia auditoria de lectura/acceso a ficha como trail formal
- no existen firma clinica legal, receta valida ni orden ejecutable
- `LabResult` y `ClinicalRisk` siguen como dominios bloqueados hasta definir fuente primaria y flujo completo
- falta politica preproduccion de cifrado, backup, retencion, PHI-safe logging y compliance

Rumbo recomendado:

- C5: documentar y disenar auditoria de lectura report-only antes de escribir nuevas superficies sensibles
- C5-01: revisar `reports/read-access-map.*` antes de decidir middleware, tabla o politica de retencion para lectura
- C5-02: revisar `reports/read-access-policy.*`; `blocking_ready=false` hasta cerrar retencion, volumen y tests
- C6: continuar ficha paciente formal v0.5 con mejoras de papel/paridad si no se duplica fuente
- C7: usar `reports/encounter-axis-map.*` como base antes de endurecer `encounter_id`
- C8: mantener documentos clinicos no firmados como borradores visibles
- C9: elevar seguridad preproduccion de report-only a politica bloqueante progresiva

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
npm run check:architecture
npm run check:e2e
npm run check
```
