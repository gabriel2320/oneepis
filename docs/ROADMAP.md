# Roadmap e Historial de Desarrollo

Este documento resume como ha crecido OneEpis y que decisiones deben seguir
guiando el desarrollo. No reemplaza `docs/CURRENT_STATE.md`; es una lectura
cronologica para humanos y agentes.

## Estado actual

Fecha de corte: 2026-06-24.

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
- No se creo agenda productiva ni API nueva para consulta.

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

### Bloque C3/C4: gobernanza ejecutable

- Se agregaron mapas y gates para dominio, trazabilidad, papel, permisos,
  contratos frontend y uso de snapshots.
- `LabResult` y `ClinicalRisk` quedaron declarados como dominios bloqueados
  permitidos hasta definir fuente primaria y flujo clinico completo.
- `check:permissions` falla si una ruta mutante clinica queda sin actor,
  auditoria o evidencia de test 403.
- `check:architecture` agrupa `check:screens`, `check:permissions`,
  `check:paper`, `check:contracts:drift` y `check:traceability`.
- CI, bootstrap Ubuntu/Windows, README, PR template y `npm run check` quedaron
  alineados con el gate arquitectonico.

### Inicio PROG-ASSISTANT-READ-01

- Se inicio el asistente clinico de solo lectura con
  `GET /api/v1/patients/{patient_id}/assistant/timeline`.
- Se agrego `POST /api/v1/patients/{patient_id}/assistant/search` como
  busqueda deterministica sobre las fuentes normalizadas del timeline.
- Se agrego `POST /api/v1/patients/{patient_id}/assistant/chart` para devolver
  series graficables de signos vitales, eventos `exam_result` y marcas de
  medicacion activa.
- El timeline une fuentes existentes: encuentros, evoluciones, eventos,
  signos vitales, problemas activos, medicacion activa, alergias activas e
  indicaciones hospitalarias.
- Las respuestas declaran `source_type`, `source_id`, fecha disponible, resumen,
  snippets, faltantes o limites; no escriben ficha ni registran auditoria de
  modificacion.
- Queda pendiente correlacion por presets antes de abrir UI dedicada.

## Principios aprendidos

- Una feature clinica entra solo si tiene flujo humano completo.
- PostgreSQL y API son la verdad; UI, papel e IA son proyecciones.
- La IA nunca firma, no escribe ficha automaticamente y no reemplaza revision humana.
- El papel no es secundario: debe revelar estado, actor, fecha y condicion de desarrollo cuando aplique.
- Los placeholders deben desaparecer cuando una ruta se vuelve real.
- Los PRs pequeños han mantenido el codigo corregible por agentes.

## Proximo rumbo

El siguiente crecimiento recomendado despues de AI-Chart Core y C3/C4 no es mas
IA ni dashboard. El foco debe ser ficha clinica formal, trazabilidad de acceso,
episodio y seguridad preproduccion:

- C5: auditoria de lectura report-only para ficha, papel, documentos sensibles,
  auditoria, AI-Chart y hospitalizacion.
- C6: ficha paciente formal v0.5 como caratula clinica, no dashboard.
- C7: `encounter_id` como eje de episodio ambulatorio/hospitalario.
- C8: documentos clinicos no firmados con estado visible de borrador/desarrollo.
- C9: seguridad preproduccion, PHI-safe logging, backup/restore, retencion,
  cifrado y auditorias de dependencias progresivamente bloqueantes.
- IA sigue como ayuda secundaria: fuente, faltante, limite, accion humana y
  auditoria antes que chat libre, RAG o escritura automatica.

Despues de eso, cualquier expansion debe pasar por la escalera OneEpis:

1. Debe existir?
2. Pertenece al flujo paciente/ficha/papel?
3. Ya lo cubre API/PostgreSQL/auditoria/permisos?
4. Puede entrar como una pantalla o accion minima?
5. Solo entonces implementar lo minimo verificable.
