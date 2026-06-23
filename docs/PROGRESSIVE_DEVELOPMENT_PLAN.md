# Progressive Development Plan

## Decision

OneEpis avanza por fases progresivas. Cada fase debe dejar una ficha usable, auditable y menos dependiente de IA generativa.

Cada fase debe cumplir `docs/VISUAL_INTELLIGENCE_COUPLING.md`: toda inteligencia nueva requiere correlato visual inmediato, accion humana clara y auditoria.

La secuencia obligatoria es:

```text
Fase 0: Simulated Clinical Intelligence
Fase 1: AI-Chart Core estable
Fase 2: Context Builder serio
Fase 3: Chat dirigido y preferencias
Fase 4: Medicamentos, examenes y pendientes
Fase 5: Documentos y propuestas estructuradas
Fase 6: Alta y epicrisis
Fase 7: Ollama local como mejora
Fase 8: Gateway externo opcional
```

No se avanza a una fase si la anterior no conserva:

- fuentes visibles
- datos faltantes
- certeza o limite declarado
- confirmacion humana para escribir ficha
- auditoria
- degradacion sin Ollama
- correlato visual editable o confirmable

## Algoritmo de Complejizacion

Cada ciclo automatico de desarrollo debe complejizar solo una dimension:

```text
leer estado -> elegir fase activa -> escoger una brecha -> reducir alcance
-> implementar en superficie existente -> validar -> documentar estado real
```

Selector de brecha:

1. Toma el primer item de `Trabajo` de la fase activa que pueda resolverse sin nueva superficie.
2. Si requiere API nueva, verifica antes que no quepa en una ruta existente.
3. Si requiere UI nueva, verifica antes que no quepa en un panel existente.
4. Si requiere modelo nuevo, verifica antes que no pueda expresarse como evento, patch, evidencia, pendiente o fuente.
5. Si requiere dependencia nueva, detente y registra la justificacion en el PR antes de implementar.

Reglas de alcance por ciclo:

- maximo una conducta clinica nueva
- maximo una superficie UI tocada
- maximo una familia de tests tocada
- cero rutas placeholder
- cero documentos nuevos salvo decision arquitectonica imposible de absorber
- cero escritura clinica sin `ClinicalPatch` o endpoint canonico con auditoria

Orden de preferencia para complejizar:

1. Mejorar explicacion de inferencias existentes.
2. Vincular inferencias con fuentes visibles.
3. Reducir falsos positivos o ambiguedad clinica.
4. Agregar faltantes contextuales por dominio.
5. Ampliar reglas deterministicas con datos ya modelados.
6. Solo despues agregar nuevo contrato API.

Condiciones de cierre:

- la fase activa queda mas explicable o mas segura
- no aumenta el numero de modulos conceptuales
- el usuario clinico ve el cambio en una pantalla existente
- los gates relevantes pasan
- `CURRENT_STATE` y este plan coinciden con lo que realmente existe

## Estado Actual

OneEpis tiene Fase 1 cerrada a nivel de producto minimo y Fase 2 iniciada. PR #1 fue revisado, endurecido y mergeado en `main` el 2026-06-23. La base ya permite:

- leer ficha longitudinal por paciente
- usar eventos clinicos como memoria estructurada
- generar borrador SOAP desde eventos
- usar barra clinica dirigida con AI Bridge
- generar propuestas revisables desde evoluciones escritas
- persistir cambios IA solo mediante `ClinicalPatch` confirmado
- auditar aceptacion, rechazo y guardado
- bloquear aceptaciones `ClinicalPatch` sin confirmacion humana obligatoria
- bloquear evoluciones AI-Chart que pretendan guardarse como firmadas/no borrador
- leer timeline longitudinal assistant desde backend sin escritura clinica
- buscar texto clinico assistant desde backend sin escritura clinica
- devolver series graficables simples desde backend sin escritura clinica
- correlacionar por presets cerrados desde backend sin escritura clinica
- funcionar con `ONEEPIS_AI_PROVIDER=local_rules` y Ollama apagado
- explicar por que un evento reciente se asocia o no a un problema activo dentro del Context Builder
- mostrar faltantes contextualizados por atencion ambulatoria, hospitalizada o desconocida
- detectar curso clinico narrativo como mejora o empeoramiento desde eventos recientes
- asociar evidencia a problemas por vocabulario clinico local explicable, no solo texto literal
- usar codigos SNOMED CT y payloads derivados de repositorios terminologicos externos cuando existan

`PROG-ASSISTANT-READ-01` queda cerrado como release `v0.4-assistant-read`.
El trabajo activo vuelve al nucleo clinico tradicional con
`PROG-PATIENT-CORE-01`. No agregar chat libre, RAG, documentos, IA externa ni
nuevas superficies IA como atajo.

## PROG-ASSISTANT-READ-01

Estado: cerrado como release `v0.4-assistant-read` el 2026-06-23, con
walkthrough humano aprobado, changelog y tag.

Objetivo: convertir OneEpis en una ficha medica tradicional aumentada que puede
leer, buscar, mostrar, graficar y correlacionar su propia historia longitudinal,
sin aumentar escritura automatica ni abrir chat libre.

Decision de arquitectura:

- el programa es de solo lectura
- no reemplaza AI-Chart ni crea dashboard central
- no usa RAG, embeddings, IA externa ni chat libre
- no toca receta, firma clinica, indicaciones ejecutables ni documentos firmados
- no escribe ficha; si en el futuro propone escritura, eso queda fuera de este
  programa y debe pasar por `ClinicalPatch`
- todas las respuestas deben incluir fuentes y declarar faltantes o limites
- la primera implementacion debe ser deterministica y funcionar con Ollama apagado

Condicion historica de entrada:

- partir desde `main` posterior al merge `14552489b3dce69c16f4c5cd90c27afe7ffba698`
- conservar verde `api`, `web`, `contracts-e2e` y contrato OpenAPI
- abrirlo como micro-PR logico, sin mezclar laboratorio, accesibilidad amplia ni releases

Orden obligatorio de ejecucion:

1. Backend schemas + timeline de lectura. Estado: implementado.
2. Busqueda deterministica. Estado: implementado.
3. Datos graficables. Estado: implementado.
4. Correlacion deterministica por presets. Estado: implementado.
5. OpenAPI y cliente web. Estado: implementado inicial.
6. UI minima solo si el backend esta verde. Estado: implementado inicial en AI-Chart.
7. Tests y documentacion canonica. Estado: tests API backend Assistant Read implementados.

Entregables backend permitidos:

```text
GET  /api/v1/patients/{patient_id}/assistant/timeline
GET  /api/v1/patients/{patient_id}/assistant/search?q=...
POST /api/v1/patients/{patient_id}/assistant/chart
POST /api/v1/patients/{patient_id}/assistant/correlate
```

Estas rutas deben consultar entidades existentes y no crear, actualizar ni
eliminar pacientes, evoluciones, eventos, signos vitales, medicamentos,
alergias, problemas, encuentros, indicaciones ni auditoria de modificacion.

Implementado inicial:

- `GET /api/v1/patients/{patient_id}/assistant/timeline`
- respuesta con `items`, `missing_data`, `warnings`, `limit`, `has_more` y `applies_changes=false`
- lectura de encuentros, evoluciones, eventos, signos vitales, medicacion activa, problemas activos y alergias activas
- cada item declara ruta fuente existente para inspeccion humana
- probado con usuario `solo_lectura` y sin crear auditoria por lectura
- `GET /api/v1/patients/{patient_id}/assistant/search?q=...`
- busqueda deterministica en dominios existentes con `results`, `missing_data`, `warnings`, `limit`, `has_more` y `applies_changes=false`
- cada resultado declara snippet, campos coincidentes y ruta fuente existente para inspeccion humana
- probado con usuario `solo_lectura`, limite, vacio, orden temporal y sin crear auditoria por lectura
- `POST /api/v1/patients/{patient_id}/assistant/chart`
- respuesta con series graficables simples, puntos numericos, fuente, limite, faltantes y `applies_changes=false`
- lee signos vitales estructurados, `lab_results` activos y eventos `clinical_events.exam_result` con payload numerico, sin migrar laboratorio historico
- probado con usuario `solo_lectura`, limite, series no soportadas, vacio y sin crear auditoria por lectura
- `POST /api/v1/patients/{patient_id}/assistant/correlate`
- respuesta con correlaciones descriptivas por presets cerrados, evidencia fuente, faltantes, limite y `applies_changes=false`
- presets implementados: `fever_infection`, `renal_medications`, `respiratory_oxygen`, `hemoglobin_bleeding` y `medication_changes`
- probado con usuario `solo_lectura`, limite, faltantes y sin crear auditoria por lectura

Alcance por endpoint:

- `timeline`: unir encuentros, evoluciones, eventos, signos vitales,
  medicamentos activos, problemas activos, alergias, `lab_results` activos e indicaciones si existen.
- `search`: buscar texto deterministico en SOAP, eventos, problemas,
  medicamentos, alergias, encuentros, notas textuales y `lab_results`.
  Estado: implementado.
- `chart`: devolver series de signos vitales, examenes desde `lab_results`
  activos y eventos legacy `exam_result`, y marcas de medicamentos como datos listos para UI. Estado: implementado inicial para signos vitales y examenes numericos; marcas de medicamentos quedan pendientes.
- `correlate`: describir relaciones temporales con presets cerrados
  `fever_infection`, `renal_medications`, `respiratory_oxygen`,
  `hemoglobin_bleeding` y `medication_changes`. Estado: implementado.

UI permitida:

- preferir integracion sobria en AI-Chart si cabe sin inflar la pagina
- permitir `/pacientes/[patientId]/contexto` solo como vista de ficha, no dashboard
- bloques maximos iniciales: Timeline, Buscar, Graficar, Correlacionar
- usar estados loading/empty/error y componentes clinicos existentes

Implementado UI inicial:

- panel `Assistant Read` integrado en `/pacientes/[patientId]/ai-chart`
- tabs compactos: Timeline, Buscar, Series y Correlacion
- cliente web tipado para timeline/search/chart/correlate
- el tab Series muestra fuentes accionables y una lectura minima de paneles de laboratorio recientes, sin crear navegacion nueva
- no se crea ruta `/contexto`, dashboard ni escritura clinica nueva

Criterios de aceptacion cumplidos:

- el asistente lee historia longitudinal autorizada
- la busqueda devuelve fuentes, no solo texto
- chart devuelve datos graficables, no imagenes ni graficos acoplados al backend
- correlate no diagnostica ni prescribe; solo relaciona fuentes y faltantes
- no hay escritura clinica nueva
- OpenAPI queda actualizado
- los tests prueban solo lectura, permisos y faltantes
- pasan `check:api`, `check:web`, `check:contract`, `check:e2e` y `check`

## PROG-PATIENT-CORE-01

Estado: activo.

Objetivo: completar nucleo paciente tradicional sin crecer IA. El primer tramo
debe usar fuentes existentes y pantallas actuales: ficha, eventos, problemas,
alergias, medicacion, laboratorio y linea longitudinal.

Trabajo permitido:

- antecedentes clinicos de solo lectura dentro de ficha
- curaduria minima de eventos como antecedentes, diagnosticos, procedimientos y planes
- laboratorio sobrio con fuente especifica por panel/resultado
- contratos futuros para agenda avanzada, firma/cierre legal de epicrisis y papel antes de UI amplia

Avances ya mergeados de este programa:

- PR #15: agenda ambulatoria minima con `ClinicalAppointment`
- PR #16: resumen ambulatorio real de solo lectura
- PR #17: indice de documentos/papel existente

Siguiente bloque obligatorio antes de otra feature: `PROG-CONSOLIDATE-01`.

## PROG-CONSOLIDATE-01

Estado: completado.

Objetivo: consolidar #15-#17, aprender de errores y preparar avance automatico
sin abrir nueva superficie clinica.

Trabajo permitido:

- reconciliar documentos canonicos
- extraer componentes web cercanos al limite de tamano
- reforzar `check:size` con reporte near-limit no bloqueante
- documentar cola de avance automatico

Avances completados:

- PR #18: reconciliacion documental post #15-#17
- PR #19: extraccion de `PatientPaperDocuments` sin cambio de conducta
- PR #20: reporte near-limit no bloqueante en `check:size`

PR-AUTO-01 completo: la cola de ejecucion automatica quedo documentada con
branch, titulo, gates y criterio de merge.

Fuera de alcance:

- API/OpenAPI/modelos nuevos
- IA nueva, dashboards, adjuntos, firma, receta valida o features clinicas nuevas

### Cola de ejecucion automatica

Reglas de ejecucion:

- partir siempre desde `main` limpio y actualizado
- abrir una sola rama por bloque y no mezclar contrato con implementacion
- no crear UI amplia si el contrato clinico todavia no esta aprobado
- no agregar backend/API/OpenAPI si el bloque es docs-only
- corregir fallos dentro de la misma rama antes de marcar ready
- fusionar solo con CI verde y docs canonicos reconciliados

| Orden | Bloque | Branch sugerida | PR title sugerido | Gates esperados | Criterio de merge |
| --- | --- | --- | --- | --- | --- |
| 1 | `PROG-POST-PRECONSULTA-01` | `codex/post-preconsult-consolidation` | `[codex] consolidate post-preconsult queue` | `npm run check:size` | #25 registrado como completado, cola nueva documentada y sin API/UI nueva |
| 2 | `PROG-DIET-01` | `codex/diet-near-limit-files` | `[codex] trim near-limit clinical files` | `npm run check:size`, `npm run check:web` | extraccion quirurgica sin cambio de conducta ni rutas/API |
| 3 | `PROG-PATIENT-CORE-POLISH-01` | `codex/patient-core-read-polish` | `[codex] polish patient core read surfaces` | `npm run check:web`, E2E ficha | antecedentes, timeline y laboratorio mas claros sin entidad/ruta/escritura nueva |
| 4 | `PROG-AMB-PRECONSULTA-PERMISSIONS-00` | `codex/preconsult-permissions-decision` | `[codex] decide preconsult permissions path` | `npm run check:size` | decision docs-only: enfermeria aprobada para PR backend; admision administrativa futura |
| 5 | `PROG-AMB-PRECONSULTA-PERMISSIONS-01` | `codex/preconsult-nursing-permissions` | `[codex] allow nursing preconsult backend` | `npm run check:api`, `npm run check:web`, `npm run check:contract` | backend/permisos/tests habilitan enfermeria sin ruta nueva ni rol admision |
| 6 | `PROG-CLINICAL-RISK-01` | `codex/clinical-risk-minimal` | `[codex] implement minimal clinical risks` | `npm run check:api`, `npm run check:web`, `npm run check:contract`, E2E visible | API/permisos/auditoria/OpenAPI/UI compacta listas, sin dashboard ni IA |

Bloques ya cerrados en esta cola: `PROG-CONSOLIDATE-01`,
`PROG-AMB-PRECONSULTA-00`, `PROG-CLINICAL-RISK-00` y
`PROG-AMB-PRECONSULTA-01`.

## PROG-AMB-PRECONSULTA-00

Estado: contrato docs-only definido.

Objetivo: definir la admision/preconsulta ambulatoria minima antes de crear UI,
API nueva o tablas nuevas.

Decision de contrato:

- reutilizar primero `ClinicalAppointment`, `ClinicalEncounter(type=ambulatory)`,
  `VitalSign` y `ClinicalEvent(event_type=clinical_note)`
- no crear ruta nueva, dashboard, modulo de admision amplio ni endpoint global
- no crear tabla `preconsults` en el primer PR; solo considerarla si la UI
  minima demuestra duplicacion real o falta de contrato estructurado
- registrar observaciones de preconsulta como evento clinico con payload
  `preconsult`, vinculado al encuentro ambulatorio cuando exista
- signos vitales siguen viviendo en `VitalSign`, no dentro de texto libre
- el estado operativo de llegada usa `ClinicalAppointment.status`: `check_in`,
  `in_progress`, `completed`, `cancelled` o `no_show`

Alcance permitido para `PROG-AMB-PRECONSULTA-01`:

- panel compacto en `/consulta/agenda` o `/consulta/pacientes/[patientId]/atencion`
- confirmar identidad local sin agregar identificadores sensibles nuevos
- registrar motivo breve, prioridad textual, signos, alergias/medicacion revisadas
  y faltantes
- enlazar a atencion ambulatoria existente
- mostrar fuentes y faltantes; IA solo lectura/resumen no persistido

Fuera de alcance:

- receta valida, orden ejecutable, firma, folio, despacho o administracion
- diagnostico autonomo, triage automatico, chat libre, RAG o IA externa
- agenda por recursos/equipos, caja, asegurador o facturacion
- pantalla de admision grande o modulo administrativo nuevo

Gates para promover a implementacion:

- `docs/SCREEN_TREE.md` contiene el contrato minimo
- `docs/CURRENT_STATE.md` declara si preconsulta sigue futura o queda
  implementada como panel minimo
- `docs/GOVERNANCE.md` mantiene la regla de contrato antes de UI amplia
- `npm run check:size` verde

## PROG-AMB-PRECONSULTA-01

Estado: completado y mergeado como PR #25.

Objetivo: agregar preconsulta ambulatoria compacta dentro de
`/consulta/pacientes/[patientId]/atencion`, sin ruta nueva, sin tabla nueva y
sin endpoint compuesto.

Decision de implementacion:

- reutilizar citas del paciente con estado `scheduled`, `check_in` o
  `in_progress`
- crear `ClinicalEncounter(type=ambulatory, status=in_progress)` con el motivo
  de la cita o el motivo breve ingresado
- registrar signos vitales opcionales en `VitalSign`; campos vacios no se
  convierten en cero
- registrar el resumen de preconsulta como `ClinicalEvent(event_type=clinical_note)`
  con `payload.preconsult`
- actualizar la cita a `in_progress`
- no emitir diagnostico, receta, orden, firma ni `ClinicalPatch`

Nota de permisos:

- la UI inicial habilita escritura solo cuando el usuario cumple permisos de
  encuentro, evento y signos; hoy eso equivale a `medico/admin/dev`
- habilitar `enfermeria` o rol futuro `admision` exige PR backend de permisos,
  tests API y actualizacion de `SCREEN_TREE`

## PROG-AMB-PRECONSULTA-PERMISSIONS-00

Estado: decision docs-only implementada.

Decision:

- `enfermeria` si debe poder registrar preconsulta avanzada, porque ya registra
  signos vitales y participa en check-in clinico
- la habilitacion debe ser backend-first: permisos, tests API, OpenAPI/contrato
  si cambia superficie y ajuste UI posterior
- `admision` no se habilita ahora: falta rol administrativo, limites de datos
  y separacion clara entre check-in administrativo y acto clinico

Fuera de alcance:

- no cambiar permisos en este PR
- no crear rol `admision`
- no crear endpoint compuesto, tabla nueva, ruta nueva ni UI nueva

Siguiente PR permitido:

- `PROG-AMB-PRECONSULTA-PERMISSIONS-01`: permitir a `enfermeria` completar
  solo el flujo existente de preconsulta, con tests API de permiso y rechazo
  para `solo_lectura`

Gates de cierre:

- `npm run check:size`
- `npm run check:web`
- E2E visible de atencion con panel de preconsulta en modo demo
- `CURRENT_STATE`, `SCREEN_TREE`, `GOVERNANCE`, `CODEX_PLAN` y registry
  reconciliados

## PROG-POST-PRECONSULTA-01

Estado: bloque activo de consolidacion docs-only.

Objetivo: cerrar memoria ejecutable posterior a PR #25, sin tocar UI ni API.

Decision de implementacion:

- marcar `PROG-AMB-PRECONSULTA-01` como completado en cola y roadmap
- registrar que la preconsulta minima queda congelada con permisos
  `medico/admin/dev`
- declarar que `enfermeria` o `admision` requieren PR backend/permisos/tests
- promover el siguiente bloque a dieta quirurgica antes de nueva clinica

Gates de cierre:

- `npm run check:size`
- worktree limpio y PR docs-only

## PROG-DIET-01

Estado: primera extraccion quirurgica completada en mesa de pacientes.

Objetivo: reducir presion de archivos near-limit sin cambiar conducta.

Prioridad de seleccion:

- elegir un solo archivo o familia cercana a 350 lineas desde el reporte de
  `check:size`
- preferir superficies que probablemente se tocaran despues: ficha/paciente,
  eventos, papel o subpaneles AI-Chart
- no modificar rutas, API, OpenAPI, permisos, textos clinicos ni diseño visible

Gates de cierre:

- `npm run check:size`
- `npm run check:web`

Resultado inicial:

- `patient-list-pages.tsx` dejo de aparecer en el reporte near-limit
- la lista y metricas de pacientes quedaron extraidas a un componente dedicado
- no cambiaron rutas, API, OpenAPI, permisos, textos clinicos ni diseno visible

## PROG-PATIENT-CORE-POLISH-01

Estado: polish de lectura implementado en ficha.

Objetivo: mejorar claridad de antecedentes, linea de tiempo y laboratorio sin
crear entidad, ruta, endpoint, IA ni escritura.

Resultado:

- antecedentes muestran conteo de fuentes usadas: problemas, alergias,
  medicacion y eventos curados
- antecedentes declaran que no crean ni corrigen antecedentes estructurados
- linea de tiempo y laboratorio declaran limites visibles y dejan la vista
  avanzada como futura
- smoke E2E de ficha cubre fuentes y limites

Gates de cierre:

- `npm run check:size`
- `npm run check:web`
- smoke E2E de ficha/clinico

## PROG-CLINICAL-RISK-00

Estado: contrato docs-only definido.

Objetivo: definir riesgos clinicos estructurados antes de crear UI, API o
tablas.

Decision de contrato:

- crear entidad futura `ClinicalRisk` solo cuando empiece la implementacion;
  no usar `ActiveProblem` como sustituto de riesgo activo
- tipos iniciales: caida, UPP, TEV, aislamiento, evento adverso y otro
- cada riesgo debe tener paciente, encuentro opcional, severidad, estado,
  fuente inspeccionable, razon, accion humana y revision
- la UI futura vive dentro de ficha, atencion u hospitalizacion; no habra
  dashboard global de riesgos en el primer PR
- IA solo puede resumir faltantes/fuentes; no calcula scores ni ejecuta
  acciones clinicas

Alcance permitido para implementacion futura:

- listar riesgos activos en ficha/pantallas clinicas existentes
- crear/corregir riesgo bajo paciente con permisos y auditoria
- marcar riesgo como resuelto o `entered_in_error`; no delete fisico
- mostrar fuente, severidad, fecha, limite y accion humana

Fuera de alcance:

- scores automaticos, ordenes, indicaciones, receta, aislamiento automatico,
  firma o `ClinicalPatch`
- ruta global `/riesgos`, dashboard de seguridad o modulo paralelo
- farmacovigilancia FAERS como regla automatica

Gates para promover a implementacion:

- `docs/SCREEN_TREE.md` contiene el contrato minimo
- `docs/CURRENT_STATE.md` declara que riesgos siguen futuros hasta PR de API/UI
- `docs/GOVERNANCE.md` mantiene reglas de no automatizacion y fuente visible
- `npm run check:size` verde

## Plan post-auditoria 2026-06-23

P0 completado: PR #1 fue revisado en modo code review, corregido en su rama, validado local/remoto, marcado ready y mergeado por squash. No abrir otro PR grande de IA hasta que el siguiente bloque tenga alcance cerrado.

P1 completado: Assistant Read Layer, solo lectura. Entrega timeline longitudinal, busqueda clinica, series graficables simples y correlacion explicable. Todo output expone fuente, limite/faltante y accion humana opcional. No chat libre, no RAG documental amplio, no IA externa y no escritura automatica.

P2 implementado minimo: examenes/laboratorio estructurados ya tienen entidad dedicada, migracion Alembic, permisos, auditoria si escribe, OpenAPI, test API y lectura puente. Mantener `clinical_events.exam_result` como compatibilidad legacy, no migrar historicos automaticamente y no ampliar UI mas alla de lectura sobria hasta completar nucleo paciente.

P3 iniciado como checklist vivo en `CURRENT_STATE`. Accesibilidad: teclado, foco visible, contraste, labels y Playwright + axe cuando el paquete quede incorporado. Performance: dataset sintetico grande, limites/paginacion por dominio e indices revisados por query real. Observabilidad: logs sin PHI, correlation ID frontend/backend, health checks utiles y errores trazables.

P4 completado para `v0.4-assistant-read`: tag, changelog, checklist de demo y walkthrough humano aprobado. Ritual semanal: paciente, hospitalizacion, evolucion, signo vital, evento, laboratorio estructurado, AI-Chart/Assistant Read, impresion y auditoria; hallazgos van a `CURRENT_STATE` o issues, no a documentos dispersos.

## Foco Inmediato

Prioridad actual:

1. Cerrar `PROG-AMB-PRECONSULTA-PERMISSIONS-00` con PR verde.
2. Si se continua preconsulta: `PROG-AMB-PRECONSULTA-PERMISSIONS-01` backend/permisos para enfermeria.
3. Si se congela preconsulta: avanzar a `PROG-CLINICAL-RISK-01`.

Hecho en este foco:

- la pagina AI-Chart volvio a quedar bajo presupuesto como orquestador
- las acciones bloqueadas explican motivo en generacion SOAP, propuestas y guardado
- AI-Chart muestra estado operativo de eventos, evoluciones, seleccion, modo y permisos
- propuestas desde evolucion muestran estado local `pendiente`, `registrando`, `registrada en ficha` o `rechazada`
- los estados persistentes de propuesta quedan resueltos por auditoria; la sesion UI mantiene el estado operativo local
- las acciones bloqueadas muestran condicion o rol habilitante
- la aplicacion de `ClinicalPatch` salio de la ruta HTTP y vive en servicio backend dedicado
- la vista de operaciones `ClinicalPatch` quedo como componente reusable, no embebida en un panel especifico
- `ClinicalPatch` rechaza targets no soportados sin escribir ficha, sin auditar aceptacion y con auditoria `unsupported`
- `ClinicalPatch` bloquea aceptaciones inseguras sin escribir ficha: falta de confirmacion humana o evolucion no borrador
- el smoke E2E cubre la presencia del flujo visual AI-Chart sin depender de Ollama

Cola corta de mantenimiento:

- no crear nuevas superficies IA; usar AI-Chart y componentes existentes
- mantener `ClinicalPatch` limitado a `clinical_event` y `evolution` hasta que exista duplicacion o necesidad real
- no ampliar laboratorio a pantalla dedicada ni crear nueva IA durante paciente-core

Fuera de foco:

- chat libre generico
- RAG
- documentos/PDF reales
- IA externa
- dashboard nuevo
- receta valida o firma real
- `packages/ai-core`, `packages/rag` o agentes externos

## Fase 0: Simulated Clinical Intelligence

Objetivo: que la ficha se comporte como IA clinica sin depender de LLM.

Componentes:

- `ClinicalIntentRouter`
- reglas locales
- plantillas
- timeline
- eventos clinicos
- validadores de faltantes
- auditoria

Implementado:

- eventos clinicos, timeline y borrador SOAP desde eventos
- `ClinicalIntent` deterministico con fuentes, faltantes, certeza, evidencia y acciones
- reglas locales de cambios 24 h, signos vitales, examenes, medicacion y revision
- `review_items` aceptables/rechazables con auditoria
- hoja SOAP editable con margen inteligente y trazabilidad S/O/A/P
- acciones propuestas que abren flujos estructurados existentes sin guardar automaticamente
- AI-Chart dividido en componentes; la pagina queda como orquestador
- AI Bridge inicial con stream tipado JSONL desde Next hacia FastAPI
- `ClinicalPatch` para propuestas que pueden escribir ficha

Resultado: la ficha ya simula inteligencia clinica util sin depender del LLM.

## Consolidacion post R-01

Estado: AI-Chart ya fue separado en componentes. La pagina paciente queda como
orquestador y no debe volver a concentrar UI detallada.

Presupuesto activo:

- `patient-ai-chart-pages.tsx`: maximo recomendado 300 lineas.
- `ai-chart-utils.ts`: no agregar reglas clinicas nuevas; moverlas al backend.
- `clinical-intent-result-panel.tsx`: si crece, extraer paneles laterales antes de sumar features.
- no crear nuevas rutas AI-Chart para tareas que caben en la pantalla actual.

Cola corta permitida antes de pasar a Fase 2: usar la lista de `Foco Inmediato`.

Criterio para cerrar Fase 1:

```text
abrir paciente -> pedir evolucion -> ver cambios 24 h -> hoja SOAP editable
-> fuentes/faltantes -> revision humana explicita -> guardar borrador auditado
-> proponer evento desde evolucion -> confirmar/rechazar patch -> ver estado visible
```

Debe funcionar con `ONEEPIS_AI_PROVIDER=local_rules` y con Ollama apagado.

## Patron AI Bridge

La frontera IA viva queda:

```text
Next UI -> Next Route Handler BFF -> FastAPI clinico -> stream tipado -> UI
```

Reglas:

- Next conversa y transmite; FastAPI decide permisos, contexto clinico y auditoria.
- El bridge no escribe ficha ni decide permisos clinicos por su cuenta.
- Todo stream debe poder expresar progreso, fuentes, advertencias y propuestas.
- El stream usa eventos tipados JSONL; la UI no debe depender de texto libre para actuar.
- No crear un Route Handler nuevo por cada idea si puede entrar por el bridge compartido.

Eventos objetivo:

```text
status -> source -> warning -> proposal -> done
```

`token` queda reservado para lenguaje generado por modelo; no debe sustituir a `proposal`.

## ClinicalPatch v0

Toda IA que proponga escritura debe converger a un parche revisable:

```text
target: evolution | clinical_event | problem | medication | document
mode: draft | suggestion
operations: add | replace | annotate
sources
warnings
requires_human_confirmation
```

La UI puede aceptar, editar o rechazar operaciones. El backend solo guarda despues de confirmacion humana explicita y registra auditoria.

Implementado v0:

- `clinical_event` como primer target real
- propuestas desde evolucion escrita incluyen `patch`
- `POST /api/v1/patients/{patient_id}/ai/confirm-clinical-patch`
- aceptacion crea evento clinico auditado
- rechazo audita sin aplicar cambios
- aceptacion exige `requires_human_confirmation=true`
- `evolution` siempre guarda borrador `draft`, nunca firma ni cierra
- la UI expone operaciones del patch antes de confirmarlo
- `evolution` crea borradores SOAP no firmados desde texto revisado

No hacer todavia:

- aplicar patch parcial desde UI compleja
- crear editor generico de patches
- mover patch a paquete compartido hasta tener duplicacion clara
- usar patch para receta, firma o indicaciones ejecutables

## Fase 1: AI-Chart Core estable

Objetivo: consolidar paciente -> eventos -> contexto -> borrador -> confirmacion -> auditoria.

Estado: cerrado como minimo producto verificable.

Ya implementado:

- `clinical_events`
- timeline
- borrador SOAP desde eventos
- guardado humano como borrador
- `ClinicalIntent`
- fuentes, certeza, faltantes, acciones
- marcas de evidencia
- contexto por problema
- baseline de evolucion previa

Pendiente que pasa a Fase 2 o mantenimiento:

- mantener `patient-ai-chart-pages.tsx` bajo presupuesto como orquestador
- sostener estados visuales y permisos al sumar nuevas inferencias
- ampliar contexto explicable sin crear chat libre ni RAG

## Fase 2: Context Builder serio

Objetivo: pasar de listas utiles a contexto clinico explicable.

Estado: iniciada con explicaciones deterministicas por problema.

Implementado inicial:

- `problem_contexts` incluye explicaciones visibles de asociacion por coincidencia textual
- eventos recientes sin problema asociado quedan agrupados con razon de revision humana
- la UI muestra explicaciones dentro de `Problemas y evidencia`
- `missing_data` describe por que falta el dato y ajusta baseline/signos vitales segun contexto asistencial
- eventos recientes con lenguaje de mejoria o empeoramiento generan reglas locales visibles en `Curso clinico`
- el curso clinico identifica dominios iniciales cuando hay senal textual suficiente: respiratorio, dolor, infeccioso, hemodinamico, metabolico o digestivo
- el curso clinico evita negaciones obvias y puede corroborar dominios respiratorio, infeccioso o hemodinamico con signos vitales recientes
- asociaciones por problema usan vocabulario local inicial por dominios respiratorio, dolor, fiebre, hipertension, diabetes y renal
- las asociaciones por vocabulario local evitan negaciones obvias para reducir falsos positivos
- si un problema tiene `code_system=SNOMED-CT` y el evento trae conceptos/ancestros SNOMED desde un repositorio externo, el Context Builder prioriza esa asociacion explicable
- los pendientes por problema activo incorporan faltantes por dominio respiratorio, metabolico, hemodinamico, infeccioso y renal
- la UI muestra para cada evidencia por problema su razon de asociacion y fuente abreviada
- `lab_results` activos aportan evidencia explicable por dominio clinico local
  y resuelven faltantes metabolicos/renales cuando corresponde

Trabajo:

- ampliar vocabulario local por problema con mas dominios clinicos
- conectar un repositorio RF2/terminology server SNOMED CT licenciado como fuente externa, sin versionar releases completos
- ampliar reglas explicitas de mejoria/empeoramiento por dominio y sumar mas contrastes estructurados
- ampliar faltantes por dominio con mas fuentes estructuradas que signos vitales,
  eventos recientes y laboratorio ya integrado
- ampliar comparacion 24 h con mas datos estructurados

Regla: toda inferencia debe mostrar por que se hizo.

## Fase 3: Chat dirigido y preferencias

Objetivo: hacer la ficha conversable sin abrir chat libre inseguro.

Trabajo:

- router de intenciones ampliado
- decisiones auditadas por accion propuesta
- preferencias de estilo confirmadas
- plantillas editables
- memoria de correcciones/rechazos

Regla: una preferencia aprendida no se aplica como verdad sin confirmacion.

## Fase 4: Medicamentos, examenes y pendientes

Objetivo: ampliar la inteligencia simulada a dominios clinicos frecuentes.

Trabajo:

- revisar cambios de medicamentos
- detectar medicamentos sin dosis o frecuencia
- detectar tratamientos sin problema asociado
- resumir tendencias de examenes
- crear pendientes clinicos auditables

Regla: el sistema advierte y ordena; no prescribe autonomamente.

## Fase 5: Documentos y propuestas estructuradas

Objetivo: convertir texto/documentos en propuestas revisables.

Trabajo:

- importar documento como fuente
- extraer antecedentes como propuesta
- crear eventos desde texto libre
- aceptar/rechazar items individualmente

Regla: un documento importado no modifica la ficha hasta confirmacion humana.

## Fase 6: Alta y epicrisis

Objetivo: cerrar casos con documentos utiles y seguros.

Trabajo:

- checklist de alta
- epicrisis preliminar
- diagnosticos de egreso
- indicaciones y controles
- pendientes antes de alta

Regla: todo documento de egreso parte como borrador no firmado.

## Fase 7: Ollama local como mejora

Objetivo: mejorar lenguaje, extraccion y resumen sin cambiar la autoridad clinica.

Trabajo:

- redaccion natural
- extraccion desde texto libre
- RAG local con fuentes
- resumen documental

Regla: Ollama enriquece; no reemplaza reglas, fuentes ni confirmacion.

## Fase 8: Gateway externo opcional

Objetivo: permitir IA externa solo bajo privacidad, autorizacion y auditoria.

Trabajo:

- anonimizado
- vista previa del payload
- autorizacion explicita
- proveedor configurable
- auditoria de envio y respuesta

Regla: nunca enviar ficha completa identificada por defecto.
