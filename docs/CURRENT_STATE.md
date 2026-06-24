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

Programa de lectura `PROG-ASSISTANT-READ-01`: cerrado como release
`v0.4-assistant-read` el 2026-06-23, con walkthrough humano aprobado,
changelog y tag publicados.

Programa activo: `PROG-PATIENT-CORE-01`.

Este programa inicia el crecimiento tradicional posterior a `v0.4`: nucleo
paciente, antecedentes leidos desde fuentes existentes, linea clinica, ficha
sobria, laboratorio minimo y preparacion contractual de ambulatorio/
hospitalizacion. No autoriza IA nueva, dashboard, chat libre ni escritura
automatica.

Estado real al 2026-06-24:

- prototipo visual aprobado como base de ficha clinica tradicional gobernada
- release `v0.4-assistant-read` cerrado y tagueado en `main`
- el siguiente objetivo de producto es `v0.5-patient-core`
- PR #31 corrige el bootstrap PostgreSQL: las migraciones
  `202606200012_medication_catalog` y `202606200015_clinical_risks` migran
  desde una base temporal limpia hasta `202606200015`
- avances iniciales de `v0.5-patient-core` ya mergeados:
  - PR #15: agenda ambulatoria minima persistida con `ClinicalAppointment`
  - PR #16: resumen ambulatorio real de solo lectura
  - PR #17: indice de documentos/papel existente desde rutas print
  - PR #25: preconsulta ambulatoria minima dentro de atencion
  - PR #32: linea de tiempo avanzada read-only dentro de ficha reutilizando
    `assistant/timeline`
  - PR #34: polish read-only de ficha/antecedentes con fuentes y faltantes mas claros
  - PR #35: enfermeria habilitada para completar solo preconsulta minima
  - PR #36: dieta frontend de clientes/contratos Assistant Read e IA clinica
- bloques de consolidacion, dieta y polish inicial de ficha quedan cerrados:
  documentacion reconciliada, `patient-list-pages.tsx` fuera del reporte
  near-limit, antecedentes con fuentes usadas y timeline/laboratorio con
  limites y faltantes visibles
- sigue faltando expansion tradicional por episodios: nucleo paciente ampliado, ambulatorio avanzado, hospitalizacion firmada/legal, adjuntos, resultados amplios y seguridad clinica
- el mapa maestro de pantallas vive en `docs/SCREEN_TREE.md` como matriz completa con ruta, modulo, momento clinico, estado, fuente de verdad, escritura, permisos, auditoria, papel, IA permitida y pendiente
- los estados validos de pantalla son `completa`, `completa/en expansion gobernada`, `preparada`, `bloqueada` y `futura`
- una pantalla preparada no cuenta como feature final y debe declarar su estado pendiente
- una pantalla bloqueada existe para evitar uso clinico hasta cumplir contrato clinico/legal; no cuenta como feature final
- `npm run check:screens` valida que toda ruta visible de `apps/web/src/app` este documentada en `docs/SCREEN_TREE.md`
- existe un Screen Capability Registry frontend en `apps/web/src/lib/screen-capabilities.ts`
- el registry declara por ruta estado, permisos, escritura, auditoria, papel, complejidad futura e IA permitida
- `npm run check:screens` tambien valida que toda ruta visible tenga `ScreenCapability` y que no haya rutas duplicadas en mapa/registry
- la barra de intenciones clinicas bloquea ejecucion directa y re-ejecucion de intenciones que la pantalla actual no declare como permitidas
- si no existe `ScreenCapability`, la UI bloquea intenciones IA por defecto
- `PROG-AMB-PRECONSULTA-01` implementa preconsulta ambulatoria minima dentro de
  `/consulta/pacientes/{patient_id}/atencion`, sin ruta, tabla ni endpoint nuevo
  y reutilizando cita, encuentro, signos vitales y evento clinico
- la preconsulta minima puede ser completada por `enfermeria`, `medico`,
  `admin` o `dev`
- el permiso de `enfermeria` es estrecho: solo crea el encuentro ambulatorio
  tecnico marcado como preconsulta y sigue bloqueado para encuentros generales,
  SOAP, medicacion, alergias, problemas e IA clinica
- `admision` sigue futura hasta existir rol administrativo y limites de
  escritura propios
- `PROG-CLINICAL-RISK-01` implementa riesgos clinicos minimos con entidad/API
  bajo paciente, permisos, auditoria, OpenAPI, UI compacta en ficha y E2E
  visible; no crea dashboard, scores automaticos ni IA nueva
- `PROG-PATIENT-CORE-NEXT-00` queda decidido y `PROG-PATIENT-TIMELINE-01`
  esta cerrado por PR #32: linea de tiempo paciente avanzada de solo lectura
  dentro de ficha, reutilizando `assistant/timeline` sin crear API, entidad o
  ruta nueva
- existe `GET /api/v1/patients/{patient_id}/assistant/timeline`
- existe `GET /api/v1/patients/{patient_id}/assistant/search?q=...`
- existe `POST /api/v1/patients/{patient_id}/assistant/chart`
- existe `POST /api/v1/patients/{patient_id}/assistant/correlate`
- no existe todavia ruta `/pacientes/[patientId]/contexto`
- existe panel web minimo `Assistant Read` dentro de `/pacientes/[patientId]/ai-chart`
- el panel Assistant Read expone badges de solo lectura, fuentes inspeccionables y ausencia de IA externa
- no se autoriza escritura clinica desde el programa
- el timeline assistant es solo lectura, no crea auditoria ni escribe ficha
- el timeline devuelve fuentes, limites y faltantes por dominio, incluyendo `lab_results` activos
- la ficha muestra linea de tiempo avanzada con filtros por dominio, fuentes,
  limites y faltantes desde `assistant/timeline`, sin entidad nueva
- la busqueda assistant es deterministica, solo lectura y devuelve fuentes/snippets
- chart assistant devuelve series graficables simples, no imagenes ni graficos acoplados
- correlate assistant devuelve relaciones descriptivas por presets cerrados, con fuentes y faltantes
- `ClinicalPatch` v0 soporta escritura confirmada solo para `clinical_event` y `evolution`
- el backend bloquea aceptar patches con `requires_human_confirmation=false`
- el backend bloquea guardar evoluciones AI-Chart que no queden en `status=draft`
- la UI de propuestas desde evolucion exige permiso AI para confirmar patches
- `PROG-PATIENT-RECORD-READ-POLISH-02` quedo cerrado por PR #34
- `PROG-AMB-PRECONSULTA-PERMISSIONS-01` quedo cerrado por PR #35
- `PROG-DIET-FRONTEND-CONTRACTS-01` quedo cerrado por PR #36
- el siguiente bloque debe elegirse pequeno: dieta near-limit restante, papel
  serio o contrato minimo paciente/ficha; no abrir IA nueva ni dominio amplio

Lecciones post #15-#17:

- cada pantalla promovida a `completa` debe actualizar `SCREEN_TREE`, `screen-capabilities.ts`, E2E smoke y este documento en el mismo PR
- no dejar placeholders visibles cuando una ruta empieza a mostrar datos reales
- evitar selectores E2E ambiguos: usar texto exacto o scope por card cuando el texto aparece en badges y descripciones
- vigilar archivos entre 300 y 350 lineas antes de agregarles comportamiento; extraer componentes pequenos primero
- mantener los documentos canonicos sincronizados para no volver a declarar como `preparada` una superficie ya completa
- validar migraciones nuevas contra una DB PostgreSQL temporal limpia; los tests
  API no sustituyen el bootstrap Alembic completo

## Backend

Router principal: `apps/api/src/oneepis_api/api/v1/routes/patients.py`.

Dominios CRUD:

- pacientes
- encuentros clinicos
- clinical entries con vinculo opcional a encuentro
- clinical events como hechos longitudinales
- laboratorio/examenes estructurados minimos como paneles y resultados
- riesgos clinicos minimos
- problemas activos
- alergias
- medicacion
- signos vitales

Medicacion con vademecum:

- existe catalogo local versionado `MedicationCatalogItem`/`MedicationDoseRule`
- existe `GET /api/v1/medication-catalog`
- existe `GET /api/v1/medication-catalog/{catalog_item_id}`
- existe `GET /api/v1/patients/{patient_id}/medication-drafting-context`
- existe `POST /api/v1/patients/{patient_id}/medications/validate-draft`
- `POST /api/v1/patients/{patient_id}/medications` revalida dosis antes de guardar
- una dosis fuera de rango curado bloquea sin `dose_override_reason`
- el override guarda snapshot de regla, fuente, alerta y justificacion en auditoria
- el fixture incluido es demo sintetico y declara `no uso clinico`
- FDA/openFDA, Drugs@FDA, FAERS, enforcement e ISP/ANAMED quedan como fuentes de evidencia para curaduria local; no se consultan en vivo desde UI clinica
- receta valida, orden ejecutable, firma, folio, despacho y administracion siguen bloqueados/futuros

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
- escrituras clinicas se reparten por permiso fino; `admin` y `dev` pueden
  operar todo el entorno local gobernado, `medico` escribe actos medicos y
  `enfermeria` queda acotada a signos/eventos/laboratorio/riesgos y
  preconsulta ambulatoria minima
- IA clinica requiere `admin`, `medico` o `dev`
- fuera de `development`, la API rechaza secreto default, usuarios default, actor dev y auth desactivada

Higiene local:

- en `development`, la API rechaza escrituras de paciente con terminos de fixtures externos conocidos
- esta guardia evita recontaminar PostgreSQL local con datos de proyectos previos
- no reemplaza permisos, auditoria ni limpieza manual de bases ya contaminadas

Permisos finos:

- matriz viva en `docs/PERMISSIONS.md`
- enfermeria puede registrar signos vitales, eventos clinicos, laboratorio
  minimo y riesgos clinicos, pero no encuentros, SOAP, medicacion, alergias,
  problemas ni IA clinica
- encuentros clinicos generales requieren rol medico/admin/dev; la excepcion
  estrecha es la preconsulta ambulatoria minima, donde `enfermeria` puede crear
  solo el encuentro tecnico de preconsulta
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
- `GET/POST/PATCH /api/v1/patients/{patient_id}/lab-panels`
- `GET/PATCH /api/v1/patients/{patient_id}/lab-panels/{panel_id}/results/{result_id}`
- factory compatible en `services/ai/provider.py`
- contrato, providers, parsing y sugerencias snapshot separados en `services/ai/*`
- Ollama es first-class en desarrollo, con fallback no bloqueante
- AI-Chart Core funciona como Nivel 0: reglas, plantillas, fuentes, faltantes, review items auditados, hoja SOAP con margen inteligente, propuestas de eventos desde evoluciones escritas y guardado por `ClinicalPatch` confirmado aunque Ollama este apagado
- las aceptaciones `ClinicalPatch` quedan limitadas por contrato: confirmacion humana obligatoria, evolucion siempre borrador no firmado y auditoria de bloqueo cuando no aplica

Assistant Read Layer:

- `GET /api/v1/patients/{patient_id}/assistant/timeline`
- `GET /api/v1/patients/{patient_id}/assistant/search?q=...`
- `POST /api/v1/patients/{patient_id}/assistant/chart`
- `POST /api/v1/patients/{patient_id}/assistant/correlate`
- solo lectura con rol de lectura de paciente
- une encuentros, evoluciones, eventos, signos vitales, medicacion activa, problemas activos y alergias activas
- busca texto en encuentros, evoluciones, eventos, signos vitales con notas, medicacion activa, problemas activos, alergias activas y resultados de laboratorio estructurados
- devuelve series de signos vitales y examenes numericos desde `lab_results` activos y eventos legacy `exam_result`
- correlaciona por presets cerrados: fiebre/infeccion, renal/medicacion, respiratorio/oxigenacion, hemoglobina/sangrado y cambios de medicacion
- cada item expone tipo, fecha, resumen y ruta fuente existente
- cada resultado de busqueda expone tipo, fecha, snippet, campos coincidentes y ruta fuente existente
- cada punto graficable expone fecha, valor, fuente y ruta fuente existente
- cada correlacion expone evidencia, resumen descriptivo y faltantes; no diagnostica ni prescribe
- declara dominios faltantes y limite aplicado
- no escribe ficha, no audita modificacion y no depende de Ollama
- UI minima integrada en AI-Chart con tabs Timeline, Buscar, Series y Correlacion
- el tab Series muestra fuentes accionables y lectura acotada de paneles de laboratorio recientes
- backend Assistant Read esta dividido por dominio en rutas/helper de timeline, busqueda, series, correlacion y utilidades comunes
- `patient_assistant.py` queda como agregador de routers y ya no requiere excepcion de tamano en `check:size`
- pendiente: decidir si `/pacientes/[patientId]/contexto` aporta valor como vista dedicada sin crear dashboard

Laboratorio estructurado:

- existe entidad minima `LabPanel`/`LabResult` para paneles y resultados de examenes
- no existe UI amplia ni navegacion propia de laboratorio todavia
- existe lectura minima de paneles/resultados recientes dentro de Assistant Read, sin escritura ni carga masiva
- existe lectura minima de paneles/resultados recientes dentro de la ficha, sin escritura, carga masiva ni navegacion nueva
- la ficha inicia antecedentes clinicos de solo lectura desde problemas, alergias, medicacion y eventos curados; antecedentes familiares/sociales, vacunas, dispositivos y diagnosticos codificados siguen pendientes de contrato
- `docs/SCREEN_TREE.md` registra contratos minimos bloqueantes para agenda avanzada/productiva, alta/epicrisis firmada y papel tradicional; no se debe crear UI amplia de esas superficies antes de cumplirlos
- `POST /api/v1/patients/{patient_id}/lab-panels` crea un panel con 1 a 100 resultados
- `PATCH` corrige paneles/resultados y usa `entered_in_error`; no existe `DELETE`
- lectura usa permisos de ficha, incluyendo `solo_lectura`
- escritura usa `admin`, `medico`, `enfermeria` o `dev`
- cada escritura genera auditoria `lab_panel.created`, `lab_panel.updated` o `lab_result.updated`
- no migra historicos ni crea automaticamente `clinical_events.exam_result`
- compatibilidad: Assistant Read combina resultados estructurados activos y eventos legacy `exam_result` para series/correlaciones
- resultados no numericos se almacenan pero no se grafican como tendencia

Hospitalizacion:

- `GET /api/v1/hospitalization/active`
- `GET/POST/PATCH /api/v1/hospitalization/beds`
- `GET/POST/PATCH /api/v1/hospitalization/patients/{patient_id}/daily-sheets`
- `GET/POST/PATCH /api/v1/hospitalization/patients/{patient_id}/indications`
- tablero `/hospitalizacion/camas` lee encuentros `hospitalization` en curso
- camas estructuradas con sala/habitacion/cama y asignacion auditada a encuentros activos
- UI `/hospitalizacion/camas` administra estados y `/hospitalizacion/camas/nueva` crea camas
- camas disponibles pueden asignarse a ingresos activos sin cama; una cama ocupada debe liberarse antes de reasignarse
- ingreso medico hospitalario minimo existe como `ClinicalEntry(kind=intake)` vinculado a encuentro `hospitalization` en curso
- `/hospitalizacion/pacientes/[patientId]/ingreso` crea borradores de ingreso con permisos medico/admin/dev y auditoria de `clinical_entry.created`
- `/print/hospitalizacion/pacientes/[patientId]/ingreso/[entryId]` imprime hoja carta por ID estricto y no equivale a firma legal
- epicrisis preliminar existe como `ClinicalEntry(kind=discharge_summary)` vinculado a encuentro `hospitalization` en curso
- `/hospitalizacion/pacientes/[patientId]/epicrisis` crea borradores de epicrisis con permisos medico/admin/dev y auditoria de `clinical_entry.created`
- `/print/hospitalizacion/pacientes/[patientId]/epicrisis/[entryId]` imprime hoja carta por ID estricto y no equivale a alta firmada
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
- la misma pantalla permite cerrar un encuentro ambulatorio en curso como `completed` usando el PATCH existente de encuentros; es cierre administrativo auditado, no firma ni receta valida
- agenda ambulatoria minima existe como `ClinicalAppointment`, con persistencia, estados, permisos y auditoria
- `/consulta/agenda` lista citas por dia, permite crear cita programada y enlaza a la atencion del paciente
- preconsulta ambulatoria minima esta integrada dentro de la atencion: toma cita
  programada/en check-in/en curso, crea encuentro ambulatorio, registra signos
  opcionales y deja evento clinico `clinical_note` con payload `preconsult`
- la preconsulta minima puede completarla `enfermeria`, `medico`, `admin` o
  `dev`; enfermeria solo obtiene el permiso tecnico necesario para ese flujo,
  no gestion general de encuentros
- rol `admision` sigue futuro
- agenda avanzada por equipos/recursos y no-show operacional siguen futuras
- `/consulta/pacientes/{patient_id}/resumen` es lectura minima real: snapshot, citas, encuentros, evoluciones, problemas, alergias y medicacion; no escribe ni emite receta/orden
- seguimiento formal, interconsultas y cierre documental ambulatorio siguen futuros

Documentos/papel:

- `/pacientes/[patientId]/documentos` es indice real de papel existente: ficha, resumen, evoluciones, ingreso y epicrisis cuando hay entradas disponibles
- adjuntos externos, consentimientos, custodia documental, firma real y receta valida siguen bloqueados/futuros

Seguridad clinica:

- riesgos clinicos estructurados tienen implementacion minima: caida, UPP, TEV,
  aislamiento, evento adverso y otro
- existe `ClinicalRisk` con paciente, encuentro opcional, tipo, severidad,
  estado, fuente inspeccionable, razon, accion humana, revision y `created_by`
- existe API bajo paciente para listar, crear, leer y corregir riesgos; no
  existe ruta global `/risks` ni dashboard de seguridad
- lectura usa permisos de ficha, incluyendo `solo_lectura`; escritura usa
  `admin`, `medico`, `enfermeria` o `dev`
- cada escritura genera auditoria `clinical_risk.created` o
  `clinical_risk.updated` con `before/after` cuando aplica
- la ficha muestra una tarjeta compacta de riesgos activos; demo declara que no
  simula seguridad clinica productiva
- no hay scores automaticos, no hay bloqueo clinico inferido, no hay IA nueva y
  no existe `ClinicalPatch` para riesgos

## Frontend

Rutas App Router bajo `apps/web/src/app`.

Capas:

- `src/app/api/ai/clinical-command/route.ts`: BFF streaming con Vercel AI SDK; orquesta FastAPI y no reemplaza la API clinica canonica
- `src/lib/api/*`: clientes API por dominio
- `src/lib/api/auth.ts`: login local y sesion actual
- `src/lib/types.ts`: agregador de contratos TypeScript por dominio
- `src/components/auth/*`: login local y badge de sesion
- `src/components/layout/app-shell.tsx`: navegacion global
- temas visuales usan tokens de superficie (`surface`, `surface-subtle`, `surface-raised`) y selector con swatch
- `src/components/clinical/patient-clinical-shell.tsx`: mesa clinica por paciente
- `src/components/clinical/patient-*-pages.tsx`: pantallas paciente importadas directo por App Router
- `/pacientes` funciona como mesa clinica de entrada con buscador, metricas operativas y lista escaneable
- navegacion paciente agrupada visualmente en Ficha, Datos, IA y Control; mobile usa selector compacto de seccion clinica
- las pantallas visibles pueden mostrar badges comunes de estado, papel, escritura e IA permitida desde el Screen Capability Registry
- `/pacientes/[patientId]/ficha` se organiza como hoja clinica viva: cabecera critica, linea longitudinal y riel contextual de faltantes/IA/acciones
- `/pacientes/[patientId]/eventos` registra hechos clinicos longitudinales
- `/pacientes/[patientId]/medicacion` integra vademecum local, favoritos, sugeridos deterministicas, historial y copia de indicaciones previas como borrador humano
- `/pacientes/[patientId]/medicacion/nueva` valida dosis contra reglas curadas y exige justificacion si hay bloqueo antes de guardar
- `/pacientes/[patientId]/ficha` muestra riesgos clinicos minimos en el riel contextual; permite registro manual y marcar resuelto solo con permisos
- `/pacientes/[patientId]/ai-chart` muestra inteligencia simulada, intenciones clinicas, propuestas revisables y hoja SOAP editable con margen inteligente
- AI-Chart muestra un flujo visual guiado: leer contexto, seleccionar evidencia, revisar propuestas, generar borrador SOAP y confirmar como borrador no firmado
- AI-Chart envia la barra clinica al BFF de Next, que delega la resolucion estructurada en FastAPI y transmite eventos tipados JSONL con AI SDK
- AI-Chart no guarda propuestas desde campos sueltos; envia `ClinicalPatch` al backend para aceptar/rechazar/guardar
- AI-Chart muestra estado operativo de eventos, evoluciones, seleccion, modo y permisos antes de generar o guardar
- AI-Chart consulta el registry para bloquear intenciones no permitidas por la pantalla antes de ejecutar botones dirigidos
- Assistant Read mantiene el panel orquestador separado de sus secciones de timeline, busqueda, series y correlacion.
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
- AI-Chart usa resultados `lab_results` activos como evidencia explicable para problemas compatibles por dominio clinico local, sin crear escritura ni auditoria de modificacion
- AI-Chart vuelve a mantener `patient-ai-chart-pages.tsx` bajo presupuesto como orquestador; el flujo de propuestas desde evolucion vive en su seccion propia
- Propuestas desde evolucion muestran estado visible `pendiente`, `registrando`, `registrada en ficha` o `rechazada` antes y despues de confirmar el `ClinicalPatch`
- Las decisiones de propuesta se consideran durables via auditoria; la UI mantiene estado local de sesion para operacion inmediata
- La vista de operaciones `ClinicalPatch` esta extraida como componente reusable para evitar inflar paneles AI-Chart
- `src/components/clinical/ambulatory-visit-pages.tsx`: atencion ambulatoria minima sobre encuentros y SOAP
- `src/components/clinical/*`: cards, widgets y pantallas clinicas
- `src/components/print/*`: hojas imprimibles
- modo papel mantiene toolbar uniforme "Vista papel" y hoja carta con footer de desarrollo cuando aplica
- las rutas print no hacen fallback silencioso a otro documento cuando el ID solicitado no existe

Tests API:

- fixtures compartidas en `apps/api/tests/conftest.py`
- cobertura paciente separada por dominios: ficha, permisos, auditoria, IA y encuentros
- cobertura hospitalizacion separada por board, camas y hoja diaria
- cobertura de riesgos clinicos prueba permisos, ownership, fuente de otro
  paciente, auditoria `before/after` y ausencia de `DELETE`
- `ClinicalPatch` cubre aceptacion, rechazo, target no soportado, bloqueo por falta de confirmacion humana y bloqueo de evolucion no borrador; targets fuera de alcance no escriben ficha y quedan auditados como `ai.clinical_patch.unsupported` o `ai.clinical_patch.blocked`

Deuda visible a resolver antes de nuevo crecimiento clinico:

- no agregar nueva clinica core sin flujo completo PostgreSQL/API/permisos/auditoria/OpenAPI/UI
- no agregar pantallas clinicas nuevas sin registrar estado explicito en `docs/SCREEN_TREE.md`
- promover pantallas preparadas a completas solo con contrato backend, permisos, auditoria si escribe, pruebas y papel cuando aplique
- mover una ruta visible bajo `apps/web/src/app` exige actualizar el mapa maestro o falla `npm run check:screens`
- mantener la regla de producto: paciente -> episodio -> acto clinico -> documento -> firma/estado -> seguimiento
- sostener `/pacientes` como mesa clinica de entrada, no como dashboard ni portada generica
- `apps/web/src/components/print/clinical-print.tsx` esta cerca del presupuesto de complejidad; no inflarlo con mas papel sin separar.
- los contratos frontend de Assistant Read e IA clinica ya se separaron de
  `clinical-record.ts`; vigilar los nuevos near-limit antes de sumar dominios.
- `apps/web/src/components/clinical/ai-chart/*` concentra subcomponentes AI-Chart; mantener `patient-ai-chart-pages.tsx` como orquestador y no volver a inflarlo.
- `npm run check:size` bloquea archivos nuevos o modificados sobre 350 lineas salvo excepcion explicita con tope y razon; Assistant Read backend ya no usa excepcion propia.
- `npm run check:screens` bloquea rutas visibles sin fila en `SCREEN_TREE` o sin `ScreenCapability`.
- `npm run check:contract` verifica OpenAPI y drift minimo Assistant Read contra los tipos TS manuales.
- Playwright E2E corre con `workers: 1` para evitar 404 transitorios del dev server al compilar rutas dinamicas en paralelo.
- tras R-01, cualquier crecimiento AI-Chart debe entrar en componentes existentes o extraer subpaneles; no agregar bloques inline grandes a la pagina.
- `apps/api/src/oneepis_api/services/clinical_intent.py` ya concentra reglas deterministicas; nuevas reglas deben agruparse por dominio o extraerse antes de crecer mucho mas.
- `apps/api/src/oneepis_api/services/clinical_patch.py` concentra aplicacion y auditoria de patches aceptados/rechazados.
- `apps/api/src/oneepis_api/api/v1/routes/patient_events.py` sigue agrupando eventos e intenciones; no refactorizar mas sin otra familia de rutas IA.
- adjuntos externos, consentimientos y receta siguen como bordes bloqueados/futuros; no expandir todos a la vez.
- watchlist de tamano: componentes web cerca del limite deben extraerse antes de crecer; `patient-record-pages.tsx` quedo cerca del techo tras el indice de papel y requiere poda preventiva.
- agenda avanzada/productiva, alta/epicrisis firmada y papel tradicional amplio siguen con contrato minimo documentado en `docs/SCREEN_TREE.md`; su proximo PR debe implementar uno solo.
- receta impresa sigue bloqueada hasta tener firma, folio, actor, fecha clinica y permisos claros.
- rondas lee hojas diarias por paciente activo; aceptable por ahora, pero requerira read-model backend si escala.

Release gates demo:

- Releases previstos: `v0.1-base-ficha`, `v0.2-hospitalizacion`, `v0.3-ai-chart-core`, `v0.4-assistant-read`.
- Cada release exige tag, changelog, CI verde, checklist de demo y plan de rollback.
- Checklist `v0.4-assistant-read`: paciente, hospitalizacion, evolucion, signo vital, evento clinico, laboratorio estructurado reciente, AI-Chart/Assistant Read, impresion y auditoria.
- Criterios `v0.4`: fuentes inspeccionables, limites/faltantes visibles, cero escritura automatica, cero chat libre, cero RAG, cero IA externa activa y compatibilidad `lab_results` + `clinical_events.exam_result`.
- Rediseño visual inicial no cambia backend, OpenAPI, rutas clinicas ni permisos; cualquier tag `v0.4` sigue requiriendo walkthrough humano y CI verde.
- Estado `v0.4-assistant-read`: walkthrough humano aprobado el 2026-06-23; changelog y tag `v0.4-assistant-read` creados sobre `main`.
- Rollback `v0.4`: desactivar superficie web Assistant Read sin tocar datos clinicos; mantener endpoints de lectura y laboratorio minimo porque no migran historicos ni escriben automaticamente.
- Pantallas preparadas no cuentan como feature completa; si se vuelven visibles deben declarar estado pendiente hasta tener backend/flujo real.
- Hallazgos del walkthrough semanal van a este documento o a issues; no crear documentos dispersos.

Accesibilidad, performance y observabilidad pendientes:

- Accesibilidad: validar teclado, foco visible, contraste y labels en `/pacientes`, ficha, AI-Chart y print; agregar Playwright + axe solo cuando el paquete y el flujo queden cerrados.
- Performance: probar ficha y AI-Chart con dataset sintetico grande, revisar limites por dominio y confirmar indices contra queries reales.
- Observabilidad: mantener logs sin PHI, exponer correlation ID frontend/backend, reforzar health checks utiles y errores trazables.

## Auditoria rapida 2026-06-23

- Ultimos bloques completados: hoja diaria, cierre, reglas de fecha, rondas de lectura, fecha clinica local, politica de indicaciones/receta, indicacion minima, atencion ambulatoria minima, mesa `/pacientes` v2, temas visuales v2, AI-Chart Core Nivel 0, PR #1 mergeado y endurecimiento `ClinicalPatch`.
- Se detecto contaminacion local de datos desde fixtures externos en PostgreSQL de desarrollo; la base local fue limpiada y el nuevo foco es blindar identidad/datos antes de crecer.
- Validacion reciente local Assistant Read UI: typecheck/lint web y contrato cliente manual actualizado.
- Validacion reciente Context Builder: problemas renales/metabolicos pueden resolver faltantes con laboratorio estructurado activo.
- Rediseño grafico-web inicial: navegacion paciente agrupada, ficha como hoja clinica viva, AI-Chart con pasos guiados, paridad papel basica y tokens clinicos V2 documentados.
- Validacion reciente rediseño visual: `npm run check:size`, `npm run check:web`, `npm run check:e2e`, `npm run check:contract` y `npm run check:api`.
- Seguridad CI: job `security-report` report-only con gitleaks, dependency review, CodeQL, `npm audit` y `pip-audit`; no bloquea merge durante piloto salvo decision explicita posterior.
- Post-prototipo: `docs/SCREEN_TREE.md` clasifica rutas reales y superficies futuras por modulo, momento clinico, estado, fuente de verdad, escritura, permisos, auditoria, papel, IA permitida y pendiente.
- Validacion remota PR #1: `api`, `web` y `contracts-e2e` verdes antes del squash merge.
- Release `v0.4-assistant-read`: changelog creado, tag publicado y walkthrough humano aprobado el 2026-06-23.
- Siguiente bloque de producto despues de `v0.4`: `PROG-PATIENT-CORE-01`, nucleo paciente tradicional y laboratorio/ficha sobria, sin nueva IA ni dashboard.

## Historial

El historial cronologico vive en `docs/ROADMAP.md`.
La guia operativa para agentes vive en `docs/CODEX_PLAN.md`.

Regla IA: todo output de Ollama es borrador, requiere revision humana y no escribe ficha automaticamente.

## Gates actuales

Comandos esperados antes de entregar cambios:

```bash
npm run check:screens
npm run check:api
npm run check:web
npm run check:contract
npm run check:e2e
npm run check
```
