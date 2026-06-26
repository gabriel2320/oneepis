# Current State

Fecha: 2026-06-26

Este documento es estado operativo vigente, no historial. El historial
cronologico vive en `docs/ROADMAP.md`; los reportes fechados son snapshots y no
fuente canonica viva.

## Estado Real Hoy

- OneEpis es una ficha clinica longitudinal con entrada por login limpio,
  `/home` como mapa fisico del hospital y mundos operativos separados para
  ambulatorio y hospitalizacion.
- La identidad clinica sigue siendo `Patient` unico; los contextos se separan
  con `ClinicalEncounter` y la ficha longitudinal reconcilia antecedentes,
  eventos, evoluciones, medicacion, alergias, riesgos, signos y resultados.
- Ambulatorio minimo existe: agenda persistida, preconsulta minima gobernada,
  atencion ambulatoria, resumen de lectura y ficha comun.
- Hospitalizacion minima existe: camas, rondas, ingreso borrador, hoja diaria,
  indicaciones borrador y epicrisis borrador; no equivale a firma, alta legal,
  orden ejecutable ni MAR.
- Documentos/papel existe como proyeccion carta e indice de papel existente;
  adjuntos externos, consentimientos y firma real siguen fuera.
- AI-Chart/Assistant Read existe como apoyo contextual gobernado; la IA resume
  y propone borradores revisables, no decide, no firma y no escribe sin
  confirmacion humana/backend.
- El registry estructurado de pantallas vive en
  `apps/web/src/lib/screen-capabilities.registry.json`; la tabla de rutas reales
  en `docs/SCREEN_TREE.md` se genera desde ese registry.

## Proximo Objetivo Unico

Reducir canon manual y mejorar confiabilidad de flujos existentes. No abrir
pantallas nuevas durante este ciclo.

Criterio de exito:

- `SCREEN_TREE` deja de funcionar como segunda base de datos manual.
- `CURRENT_STATE` queda bajo 180 lineas y solo contiene estado vigente.
- Los PRs futuros declaran presupuesto de canon.
- Los tests protegen contratos clinicos/semanticos, no frases cosmeticas.

Criterio de no-hacer:

- No crear nueva pantalla clinica.
- No crear modulo de IA nuevo.
- No promover receta, firma, orden ejecutable, UCI, pabellon, adjuntos o
  consentimientos productivos.
- No abrir PR docs-only salvo que evite dano clinico, seguridad rota, setup roto
  o claim publico falso.

## Gates Obligatorios

- Todo cambio: `npm run check:toolchain`.
- Pantallas/rutas/registry: `npm run check:screens`.
- API o permisos backend: `npm run check:api`.
- UI: `npm run check:web`.
- OpenAPI: `npm run check:contract`.
- Flujo visible o papel: `npm run check:e2e`.
- Cambios transversales: `npm run check`.

CI agrega:

- `security-report`: `gitleaks` bloqueante; dependency review, CodeQL, OSV npm
  advisory check y `pip-audit` report-only hasta politica explicita.
- `postgres-alembic`: PostgreSQL 15, `alembic upgrade head` desde cero y smoke
  `downgrade -1`/`upgrade head`.

## Riesgos Vivos

- Produccion sanitaria: OneEpis no esta listo para uso clinico real ni software
  certificado.
- Seguridad: faltan secretos formales, cifrado, backups/restore, retencion,
  auditoria de accesos, logs PHI-safe y control contextual por institucion/equipo.
- Identidad: auth local sirve para desarrollo; usuarios persistentes, sesiones
  productivas, revocacion y recuperacion institucional siguen pendientes.
- Permisos: RBAC global actual es minimo; ABAC contextual sigue futuro.
- IA externa: bloqueada hasta gateway PHI, anonimizacion, autorizacion, auditoria
  y politica explicita.
- Legal clinico: firma, receta valida, orden ejecutable, MAR, consentimientos y
  adjuntos productivos siguen bloqueados.

El checklist versionado de no-produccion vive en
`docs/NO_PRODUCTION_CHECKLIST.md`.

## Decisiones Activas

- Paciente une; encounter separa; timeline reconcilia; auditoria prueba; IA
  resume, no decide.
- `screen-capabilities.registry.json` es la fuente de verdad estructurada para
  rutas visibles; `docs/SCREEN_TREE.md` conserva narrativa clinica y la tabla
  generada.
- `docs/CLINICAL_SCENARIO_AUDIT.md` define el walkthrough clinico minimo:
  consulta ambulatoria, hospitalizacion con indicacion borrador y paciente con
  riesgo/alergia/medicacion.
- `npm` 11.13.0 es el package manager oficial; pnpm queda diferido a PR dedicado.
- Los estados validos de pantalla son `completa`,
  `completa/en expansion gobernada`, `preparada`, `bloqueada` y `futura`.
- Una pantalla completa no autoriza claims legales: si hay borrador, guardrail o
  flujo minimo, debe declararse `completa/en expansion gobernada`.
- La proxima mejora debe atravesar un paciente ficticio por un flujo real antes
  que agregar mapa, copy o canon narrativo.
