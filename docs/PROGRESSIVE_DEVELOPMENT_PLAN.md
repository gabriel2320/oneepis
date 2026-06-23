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

El proximo trabajo puede preparar Fase 2 solo si conserva esta base. No agregar
chat libre, RAG, documentos o IA externa como atajo.

## PROG-ASSISTANT-READ-01

Estado: programa aceptado como extension cerrada de Fase 2, iniciado por micro-PR backend. La condicion P0 de gobernanza quedo cumplida con PR #1 mergeado y CI remoto verde.

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

Condicion de entrada:

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
  medicamentos activos, problemas activos, alergias e indicaciones si existen.
- `search`: buscar texto deterministico en SOAP, eventos, problemas,
  medicamentos, alergias, encuentros y notas textuales. Estado: implementado.
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

Criterios de aceptacion:

- el asistente lee historia longitudinal autorizada
- la busqueda devuelve fuentes, no solo texto
- chart devuelve datos graficables, no imagenes ni graficos acoplados al backend
- correlate no diagnostica ni prescribe; solo relaciona fuentes y faltantes
- no hay escritura clinica nueva
- OpenAPI queda actualizado
- los tests prueban solo lectura, permisos y faltantes
- pasan `check:api`, `check:web`, `check:contract`, `check:e2e` y `check`

## Plan post-auditoria 2026-06-23

P0 completado: PR #1 fue revisado en modo code review, corregido en su rama, validado local/remoto, marcado ready y mergeado por squash. No abrir otro PR grande de IA hasta que el siguiente bloque tenga alcance cerrado.

P1 activo permitido: Assistant Read Layer, solo lectura. Debe entregar timeline longitudinal, busqueda clinica, series graficables simples y correlacion explicable. Todo output debe exponer fuente, limite/faltante y accion humana opcional. No chat libre, no RAG documental amplio, no IA externa y no escritura automatica.

P2 implementado minimo: examenes/laboratorio estructurados ya tienen entidad dedicada, migracion Alembic, permisos, auditoria si escribe, OpenAPI, test API y lectura puente. Mantener `clinical_events.exam_result` como compatibilidad legacy, no migrar historicos automaticamente y no ampliar UI mas alla de lectura/correccion controlada hasta cerrar `v0.4-assistant-read`.

P3 pendiente: accesibilidad, performance y observabilidad. Agregar checklist vivo en docs existentes cuando empiece el bloque. Accesibilidad: teclado, foco visible, contraste, labels y Playwright + axe. Performance: dataset sintetico grande, limites/paginacion por dominio e indices revisados por query real. Observabilidad: logs sin PHI, correlation ID frontend/backend, health checks utiles y errores trazables.

P4 pendiente: releases y validacion humana. Releases demo previstos: `v0.1-base-ficha`, `v0.2-hospitalizacion`, `v0.3-ai-chart-core`, `v0.4-assistant-read`. Cada release exige tag, changelog, CI verde, checklist de demo y rollback. Ritual semanal: paciente, hospitalizacion, evolucion, signo vital, evento, AI-Chart, impresion y auditoria; hallazgos van a `CURRENT_STATE` o issues, no a documentos dispersos.

## Foco Inmediato

Prioridad dentro de Fase 2:

1. Assistant Read Layer de solo lectura, si se mantiene como micro-PR.
2. Context Builder serio: ampliar asociaciones por problema y explicar inferencias.
3. AI Bridge unico: no crear nuevos Route Handlers de IA por caso de uso.
4. Refactor minimo: extraer helpers de patch solo si aparece duplicacion real.
5. Mantener permisos visibles y estados de patch en cada nueva accion.

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
- no ampliar laboratorio ni accesibilidad amplia dentro del PR de Assistant Read

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

Trabajo:

- ampliar vocabulario local por problema con mas dominios clinicos
- conectar un repositorio RF2/terminology server SNOMED CT licenciado como fuente externa, sin versionar releases completos
- ampliar reglas explicitas de mejoria/empeoramiento por dominio y sumar mas contrastes estructurados
- ampliar faltantes por dominio con mas fuentes estructuradas que signos vitales y eventos recientes
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
