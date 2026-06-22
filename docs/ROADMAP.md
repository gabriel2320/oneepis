# Roadmap e Historial de Desarrollo

Este documento resume como ha crecido OneEpis y que decisiones deben seguir
guiando el desarrollo. No reemplaza `docs/CURRENT_STATE.md`; es una lectura
cronologica para humanos y agentes.

## Estado actual

Fecha de corte: 2026-06-21.

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

## Principios aprendidos

- Una feature clinica entra solo si tiene flujo humano completo.
- PostgreSQL y API son la verdad; UI, papel e IA son proyecciones.
- La IA nunca firma, no escribe ficha automaticamente y no reemplaza revision humana.
- El papel no es secundario: debe revelar estado, actor, fecha y condicion de desarrollo cuando aplique.
- Los placeholders deben desaparecer cuando una ruta se vuelve real.
- Los PRs pequeños han mantenido el codigo corregible por agentes.

## Proximo rumbo

El siguiente crecimiento recomendado despues de PR-064:

- fortalecer temas visuales v2 con tokens clinicos reales;
- sostener `/pacientes` como mesa clinica de entrada;
- no crear dashboard nuevo ni laboratorio visual pegado al core;
- mantener paciente, ficha y papel como centro.

Despues de eso, cualquier expansion debe pasar por la escalera OneEpis:

1. Debe existir?
2. Pertenece al flujo paciente/ficha/papel?
3. Ya lo cubre API/PostgreSQL/auditoria/permisos?
4. Puede entrar como una pantalla o accion minima?
5. Solo entonces implementar lo minimo verificable.
