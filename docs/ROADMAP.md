# Roadmap e Historial de Desarrollo

Este documento resume como ha crecido OneEpis y que decisiones deben seguir
guiando el desarrollo. No reemplaza `docs/CURRENT_STATE.md`; es una lectura
cronologica para humanos y agentes.

## Estado actual

Fecha de corte: 2026-06-23.

OneEpis ya tiene una base clinica E2E real:

- Next.js + Tailwind + shadcn/ui como mesa clinica.
- FastAPI + Pydantic como API validada.
- PostgreSQL + SQLAlchemy + Alembic como fuente de verdad clinica.
- OpenAPI como contrato frontend-backend.
- Auth local, roles, permisos y auditoria por escritura.
- Ollama local first-class, opcional y siempre como borrador.
- Modo papel serio para ficha, evolucion, resumen, hoja diaria, ronda e indicacion.

## Historial por bloques

### Base inicial

- Se creo el monorepo con `apps/web`, `apps/api`, `packages/contracts`, `infra` y `docs`.
- Se definio el stack clinico principal: Next.js, FastAPI, PostgreSQL, SQLAlchemy, Alembic y OpenAPI.
- Se conecto el flujo paciente -> ficha -> evolucion SOAP -> API -> base de datos -> auditoria.
- Se dejo `NEXT_PUBLIC_DEMO_MODE=true` como modo demo explicito, no como fuente de verdad.

### PR-018 a PR-025: mesa clinica viva e IA local

- Ollama entro como proveedor local principal en desarrollo, desacoplado y no obligatorio.
- Se agrego estado IA, sugerencias por paciente y revision de borradores SOAP.
- Se creo la shell clinica por paciente con cabecera persistente y navegacion lateral.
- Se agregaron temas visuales, modo oscuro y componentes clinicos base.
- Se reforzo el modo papel con footer de desarrollo y rutas print.
- Playwright entro como smoke visual ligero.

### PR-026 a PR-032: seguridad, permisos y ficha auditable

- Se agrego autenticacion local con roles `admin`, `medico`, `enfermeria`, `solo_lectura` y `dev`.
- Se bloqueo configuracion insegura fuera de `development`.
- Se definio matriz de permisos clinicos.
- Se reforzo auditoria con actor, correlation ID, request path y before/after.
- Se agrego estado de ficha, contexto asistencial y problemas activos.
- Encuentros clinicos quedaron como puente para consulta y hospitalizacion.
- Evoluciones SOAP pueden vincularse a encuentros.

### PR-033 a PR-036: hospitalizacion basal

- Se creo tablero hospitalario simple desde encuentros `hospitalization` activos.
- Camas hospitalarias pasaron a modelo estructurado con sala, habitacion y cama.
- Se agrego administracion UI de camas y asignacion auditada de ingresos activos.
- Se mantuvo hospitalizacion como flujo clinico, no como dashboard central.

### PR-037 a PR-045: endurecimiento y dieta

- CI quedo alineado con gates oficiales.
- Se normalizaron pocos comandos raiz: API, web, contrato, E2E y check completo.
- Se dividieron archivos grandes de paciente y backend sin cambiar comportamiento.
- Se retiro barrel temporal frontend.
- Se fortalecio el modo papel como gate clinico.

### PR-046 a PR-051: gobierno anti-inflacion

- Se codifico la doctrina anti-inflacion en `docs/GOVERNANCE.md`.
- Se alinearon guias para agentes y gates oficiales.
- Se retiro legacy demo frontend.
- Se hizo dieta UI, IA backend y tests API por dominio.
- La regla quedo clara: paciente/ficha/papel primero; dashboards, labs e IA como superficies laterales.

### PR-052 a PR-059: hoja diaria y ronda hospitalaria

- Hoja diaria hospitalizada entro como flujo completo: PostgreSQL, API, permisos, auditoria, UI y print.
- Se agrego edicion dedicada, estado `draft/closed` y bloqueo de edicion al cerrar.
- La fecha de hoja diaria se valida contra la ventana del ingreso usando fecha clinica local `America/Santiago`.
- Rondas hospitalarias quedaron como lectura desde ingresos activos, camas y ultimas hojas diarias.
- Se agrego papel de ronda hospitalaria sin crear escritura nueva.

### PR-060 a PR-062: indicaciones y consulta minima

- Se documento politica de indicaciones y receta antes de crear producto nuevo.
- Indicacion hospitalaria minima entro como borrador gobernado:
  PostgreSQL, API, permisos, auditoria, OpenAPI, UI y print.
- No existe firma real, receta valida ni ejecucion de orden hospitalaria.
- Atencion ambulatoria minima quedo conectada usando endpoints existentes:
  crea encuentro ambulatorio y evolucion SOAP vinculada.
- No se habia creado agenda productiva ni API nueva para consulta en esta etapa.

### PR-063: limpieza de identidad local

- Se detecto contaminacion de datos de desarrollo con fixtures externos en PostgreSQL local.
- Se limpio la base local y se agrego una guardia `development` para rechazar nombres de paciente con terminos de proyectos previos conocidos.
- La entrada `/pacientes` se reafirmo como mesa clinica sobria, no como dashboard ni landing page.
- El siguiente bloque debe mejorar temas visuales sin sumar dependencias ni capas nuevas.

### PR-064: endurecimiento post-auditoria

- Las rutas print dejaron de hacer fallback silencioso a otro documento cuando el ID solicitado no existe.
- El build web dejo de depender de Google Fonts y usa una pila tipografica local del sistema.
- Los scripts API/contrato usan `.venv/bin/python` para no depender del Python global de la maquina.
- `npm run check` quedo validado completo con API, web, contrato y E2E.

### PR-065: mesa `/pacientes` v2

- `/pacientes` se fortalecio como mesa clinica de entrada con buscador, metricas operativas y lista escaneable.
- Se mantuvo paciente/ficha/papel como centro, sin crear dashboard nuevo ni dependencia visual nueva.
- Se agrego smoke E2E para fijar la superficie como work queue clinica en desktop y mobile.

### PR-066: temas visuales v2

- Se agregaron tokens de superficie por tema para separar fondo, shell y areas elevadas sin dependencia nueva.
- La navegacion global usa superficies tematicas y estados activos mas claros en desktop y mobile.
- El selector de tema muestra un swatch persistente para hacer visible la plantilla activa.
- Se mantuvo el cambio como refinamiento transversal, sin nuevas pantallas ni dashboard.

### Bloque AI-Chart Core Nivel 0

- Se agrego `clinical_events` como columna de hechos longitudinales.
- AI-Chart quedo como ficha inteligente simulada: reglas, plantillas, fuentes, faltantes y auditoria.
- Se agrego router deterministico de intenciones clinicas y barra dirigida, sin chat libre generico.
- La comparacion 24 h muestra hallazgos por dominio, estado visual y fuente por hallazgo.
- `review_items` permite aceptar/rechazar propuestas sin aplicar cambios automaticos a la ficha.
- El historial visual de decisiones muestra actor, fecha y evento de auditoria.
- El borrador SOAP desde eventos se muestra como hoja carta editable con margen inteligente persistente.
- El principio sigue siendo Nivel 0 primero: la ficha debe ser util aunque Ollama este apagado.

### Release v0.4-assistant-read

- Assistant Read quedo como capa de lectura clinica de solo lectura dentro de AI-Chart.
- Timeline, busqueda, series y correlacion exponen fuentes, limites y datos faltantes.
- Laboratorio estructurado minimo se lee en Assistant Read y en la ficha sin pantalla nueva ni dashboard.
- La ficha muestra una linea de tiempo completa minima usando eventos y evoluciones existentes.
- La IA por pantalla queda cerrada por `ScreenCapability`; sin capability no se ejecuta intencion IA.
- El walkthrough humano fue aprobado el 2026-06-23.
- El changelog del release vive en `CHANGELOG.md`.
- El tag `v0.4-assistant-read` queda publicado sobre `main`.

### PROG-PATIENT-CORE-01: nucleo paciente tradicional

- Se cierra la expansion IA y se vuelve al tronco de ficha tradicional.
- La ficha inicia antecedentes clinicos de solo lectura desde problemas, alergias,
  medicacion y eventos curados, sin ruta nueva ni backend nuevo.
- La pantalla de eventos agrega curaduria minima para antecedentes, diagnosticos,
  procedimientos y planes usando `clinical_events`.
- Laboratorio queda como lectura sobria en ficha/AI-Chart, con fuente especifica
  por panel/resultado y sin dashboard dedicado.
- Atencion ambulatoria agrega cierre administrativo minimo del encuentro usando
  el contrato existente de `ClinicalEncounter`; no equivale a firma ni receta.
- Ingreso medico hospitalario entra como borrador `ClinicalEntry(kind=intake)`
  vinculado a hospitalizacion activa, con papel carta propio por ID estricto.
- Epicrisis preliminar entra como borrador
  `ClinicalEntry(kind=discharge_summary)` vinculado a hospitalizacion activa,
  con papel carta propio por ID estricto.
- Agenda ambulatoria minima queda implementada con `ClinicalAppointment`.
- Resumen ambulatorio dedicado deja de ser placeholder y queda como lectura real
  de snapshot, citas, encuentros, evoluciones, problemas, alergias y medicacion.
- Documentos/papel deja de ser placeholder y queda como indice de ficha, resumen,
  evoluciones, ingreso y epicrisis imprimibles cuando la fuente existe.
- Agenda avanzada/productiva, alta/epicrisis firmada y papel firmado/legal
  quedan pendientes de contrato backend antes de UI amplia.
- El mapa maestro registra contratos minimos bloqueantes para agenda avanzada,
  atencion ambulatoria cerrable, ingreso medico hospitalario, epicrisis borrador
  implementada y papel tradicional.

### PROG-CONSOLIDATE-01: consolidacion post #15-#17

- Estado: en cierre antes de abrir otra feature clinica.
- Objetivo: reconciliar documentacion canonica, podar componentes cerca del
  limite de tamano, reforzar guardrails y dejar cola de avance automatico.
- Alcance permitido: docs canonicos, extraccion de componentes sin cambio de
  conducta, reporte near-limit no bloqueante y reglas E2E mas precisas.
- Fuera de alcance: endpoints nuevos, OpenAPI, IA nueva, adjuntos, firma,
  receta valida, agenda avanzada o pantallas grandes.
- Cola posterior: consolidacion post-#25, dieta near-limit, polish de nucleo
  paciente, decision de permisos de preconsulta y riesgos clinicos minimos,
  con branch, titulo, gates y criterio de merge definidos en
  `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`.

### PROG-AMB-PRECONSULTA-00: contrato de admision/preconsulta

- Estado: contrato docs-only definido antes de implementar.
- Decision: reutilizar `ClinicalAppointment`, `ClinicalEncounter`,
  `VitalSign` y `ClinicalEvent`; no crear tabla ni ruta nueva en el primer PR.
- Alcance futuro permitido: panel compacto en agenda/atencion para check-in,
  motivo, signos, revision alergias/medicacion y faltantes.
- Fuera de alcance: receta, orden, firma, triage automatico, IA externa,
  dashboard o modulo administrativo amplio.

### PROG-AMB-PRECONSULTA-01: preconsulta minima

- Estado: completado y mergeado como PR #25.
- Decision: panel compacto que reutiliza citas del paciente, crea encuentro
  ambulatorio, registra signos vitales opcionales y deja evento clinico con
  `payload.preconsult`.
- Alcance: preparar la atencion humana; no diagnostica, no receta, no firma,
  no emite orden y no agrega IA.
- Restriccion de permisos: usa permisos existentes `medico/admin/dev`;
  `enfermeria`/`admision` quedan para PR backend especifico.

### PROG-POST-PRECONSULTA-01: consolidacion post #25

- Estado: siguiente micro-PR docs-only.
- Decision: no abrir clinica nueva inmediatamente despues de preconsulta.
- Alcance: registrar #25 como completado, mover la cola a dieta quirurgica y
  dejar congelada la decision de permisos.
- Fuera de alcance: UI, API, OpenAPI, IA, dashboard, firma, receta y riesgos.

### PROG-DIET-01: dieta near-limit inicial

- Estado: primera extraccion completada.
- Decision: empezar por `patient-list-pages.tsx`, porque estaba en 344/350 y
  es superficie probable de crecimiento futuro.
- Resultado: lista y metricas de pacientes extraidas a componente dedicado.
- Fuera de alcance: cambios de conducta, textos, rutas, API, OpenAPI y diseno.

### PROG-CLINICAL-RISK-00: contrato de riesgos clinicos

- Estado: contrato docs-only definido antes de implementar.
- Decision: crear entidad futura de riesgos clinicos si se implementa; no usar
  `ActiveProblem` para mezclar diagnosticos con riesgos activos.
- Alcance futuro permitido: riesgos de caida, UPP, TEV, aislamiento, evento
  adverso y otros, con severidad, estado, fuente y accion humana.
- Fuera de alcance: scores automaticos, ordenes, receta, firma, IA externa,
  dashboard global o `ClinicalPatch`.

## Principios aprendidos

- Una feature clinica entra solo si tiene flujo humano completo.
- PostgreSQL y API son la verdad; UI, papel e IA son proyecciones.
- La IA nunca firma, no escribe ficha automaticamente y no reemplaza revision humana.
- El papel no es secundario: debe revelar estado, actor, fecha y condicion de desarrollo cuando aplique.
- Los placeholders deben desaparecer cuando una ruta se vuelve real.
- Los PRs pequeños han mantenido el codigo corregible por agentes.

## Proximo rumbo

El siguiente crecimiento recomendado despues de `v0.4-assistant-read`:

- sostener `/pacientes` como mesa clinica de entrada, no como dashboard;
- no crear dashboard nuevo ni laboratorio visual pegado al core;
- mantener paciente, ficha y papel como centro.
- congelar nueva IA hasta completar el nucleo paciente tradicional.
- complejizar antecedentes, diagnosticos historicos y linea longitudinal dentro de ficha.
- preparar contratos de agenda avanzada, firma/cierre legal de epicrisis y papel amplio antes de crear UI amplia.
- elegir solo uno de esos contratos por PR cuando empiece la implementacion.
- seguir `docs/AI_CHART_INTERACTION_VISION.md` para intenciones clinicas, fuentes, certeza, faltantes, confirmacion humana y gateway externo futuro.
- tratar `docs/SIMULATED_CLINICAL_INTELLIGENCE.md` como Nivel 0 obligatorio: reglas, plantillas, timeline, validadores, preferencias y auditoria antes de depender de Ollama.
- usar `docs/GOVERNANCE.md` como mapa de decision para evitar inflar codigo o documentos.
- vincular frases del borrador SOAP con fuentes concretas antes de ampliar documentos, alta, preferencias o API externa.

Despues de eso, cualquier expansion debe pasar por la escalera OneEpis:

1. Debe existir?
2. Pertenece al flujo paciente/ficha/papel?
3. Ya lo cubre API/PostgreSQL/auditoria/permisos?
4. Puede entrar como una pantalla o accion minima?
5. Solo entonces implementar lo minimo verificable.
