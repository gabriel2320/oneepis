# Codex Plan

Guia breve para cambios hechos por agentes.

Fuentes canonicas:

- Historial: `docs/ROADMAP.md`
- Estado operativo: `docs/CURRENT_STATE.md`
- Decision anti-inflacion: `docs/GOVERNANCE.md`
- Rutas y capacidades: `docs/SCREEN_TREE.md`
- Fases AI-Chart: `docs/PROGRESSIVE_DEVELOPMENT_PLAN.md`

## Regla Madre

Construir OneEpis por ladrillos clinicos verificables:

```text
1 objetivo clinico
1 cambio acotado
tests/gates
OpenAPI actualizado si cambia API
docs minimas
sin datos reales
```

## Ciclo Correctivo Activo

Foco: limpiar UX clinica y frenar inflacion, no abrir HIS macro.

Congelamiento: sin rutas nuevas, sin `/inicio`, sin dashboard, sin bandeja de
acciones, sin macro HIS en UI, sin IA nueva. Docs-only solo por seguridad, claim
falso, setup roto o permiso contradictorio.

Presupuesto por PR: 1 pantalla, 1 comportamiento, <=4 archivos, <=1 test, <=1 doc
(solo si cambia estado real), <=300 additions, 0 rutas nuevas, 0 docs nuevos,
0 dependencias nuevas.

Carriles de PR:

- `fast`: bug acotado, test existente dirigido, sin cambio de contrato ni pantalla.
  Gates locales: `npm run check:toolchain`, `npm run check:api:target -- <test>`
  si toca API, o `npm run check:web` si toca UI.
- `clinical`: permisos, auditoria, IA, medicacion, diagnosticos, escritura clinica o
  seguridad. Gates locales: `npm run check:toolchain`, `npm run check:api`,
  y `npm run check:contract` si cambia API.
- `surface`: ruta, copy clinico visible, papel, registry o flujo E2E. Gates locales:
  `npm run check:toolchain`, `npm run check:web`, `npm run check:screens`,
  y E2E dirigido si cambia una ruta sensible.
- `release`: merge o barrido previo. Gate completo: `npm run check`.

El carril `fast` ahorra tiempo local, pero no reemplaza CI ni autoriza merge si el
cambio toca seguridad clinica, permisos, auditoria, OpenAPI, registry o datos.

Paquete de contexto por PR (ahorro de tokens): cargar solo (1) Estado Real +
Proximo Objetivo de `CURRENT_STATE.md`; (2) Anti-Canonitis + Congelamiento de
`GOVERNANCE.md`; (3) el archivo de pantalla tocado; (4) el E2E relacionado;
(5) el diff actual. No cargar todo el repo ni el historial de PRs.

Guard de copy: `apps/web/tests/e2e/clinical-smoke.spec.ts` falla si en rutas
clinicas visibles aparece `Canon ambulatorio`, `workflow_kind`,
`ClinicalEncounter`, `Ollama`, `medico/admin/dev`, `dashboard`,
`acciones disponibles` o `bandeja operativa`. No bloquear estos terminos en docs
ni en tests, solo en copy renderizado.

El mismo smoke bloquea etiquetas positivas exactas de receta, firma,
dispensacion, administracion, MAR y orden ejecutable en rutas clinicas sensibles.
Los terminos pueden aparecer solo como limite explicito, futuro bloqueado o
estado no ejecutable.

## No Negociable

- No usar datos reales ni datos demo realistas.
- No implementar diagnostico autonomo.
- No firmar ni escribir ficha desde IA.
- No imprimir receta clinica valida sin firma, folio, actor, fecha clinica y permisos claros.
- No agregar dependencias sin justificacion.
- No dejar TypeScript roto.
- No dejar endpoints sin tests.
- Toda escritura clinica debe tener actor, permisos, auditoria y `correlation_id`.
- Todo cambio de API debe actualizar `packages/contracts/openapi.json`.
- Frontend no debe usar datos demo salvo `NEXT_PUBLIC_DEMO_MODE=true`.
- Ninguna ruta clinica o print con ID en URL puede mostrar un primer registro como fallback.
- Ningun archivo clinico nuevo debe superar 350 lineas sin excepcion explicita en `scripts/check-file-size.mjs`.

## Loop De Trabajo

1. Leer `docs/CURRENT_STATE.md`, `docs/GOVERNANCE.md` y el doc del dominio tocado.
2. Entender cambios existentes en el working tree sin revertir trabajo ajeno.
3. Implementar solo el objetivo.
4. Ejecutar gates proporcionales al cambio.
5. Actualizar docs solo si cambia comportamiento o decision.
6. Entregar resumen, pruebas y riesgos.

## Handoff 2026-07-01

Estado al cierre:

- `main` sincronizado con `origin/main`.
- PRs stale #265 y #272 cerrados y reemplazados desde `main` actual.
- Ultimos PRs cerrados: #259 indice global de appointments admin/dev-only,
  #263 UX no-demo de `/pacientes` con lista autorizada vacia, #267 clinical
  risks ABAC dev-only, #268 vital signs ABAC dev-only, #269 labs ABAC dev-only,
  #270 patient context ABAC dev-only, #271 encounters ABAC dev-only, #273
  slimming de `patient_events.py`, #274 clinical events/timeline ABAC dev-only y
  #275 clinical entries ABAC dev-only, #276 refresh docs seguridad/auditoria,
  #277 clinical orders ABAC dev-only, #278 hospital drafts ABAC dev-only, #279
  gate transversal de read-enforcement patient-scoped, #281 gate por handler
  para read-enforcement patient-scoped, #282 contrato shadow de escrituras
  clinicas, #283 guard de lecturas patient-scoped sin audit, #284 inventario
  ejecutable de rutas/superficies patient-scoped, #285 write ABAC dev-only para
  signos vitales y #286 contrato de politica `security-report`.
- Avance ABAC dev-only actual: `GET /api/v1/patients`, `GET patient`,
  `GET record`, appointments patient-scoped, allergies, active problems,
  medications y medication drafting context, encounters, clinical entries,
  clinical events/timeline, clinical orders, clinical risks, vital signs,
  lab panels/results, patient context, AI patient-scoped, Assistant Read
  timeline/search/chart/correlation, hospital daily sheets, hospital
  indications y `GET /api/v1/hospitalization/active`
  detras de `ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`.
- `GET /api/v1/appointments` es indice global admin/dev-only. La UI de agenda
  global ya respeta esa frontera; las citas patient-scoped siguen siendo el
  carril clinico normal.
- `GET /api/v1/patients` ya emite `patient_index.read` minimizado. Con
  `ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`, admin/dev conservan indice global y
  roles clinicos ven solo pacientes con relacion asistencial activa. Sin
  enforcement, mantiene la navegacion visible de `/pacientes` y selectores
  clinicos.
- Signos vitales es la primera escritura clinica con write ABAC dev-only para
  create/update/delete. El resto de escrituras sigue sin write ABAC y ninguna
  escritura tiene ABAC runtime productivo.
- `security-report` bloquea Gitleaks y OSV npm high/critical; dependency
  review, CodeQL y `pip-audit` siguen report-only con contrato de baseline,
  owner, waiver y SLA antes de promoverlos.
- Barrido release post #286: `npm run check` completo paso fuera del sandbox
  con API, web, contract y E2E verdes.

Retomar con PRs pequenos, en este orden:

1. Continuar write ABAC dev-only por una segunda superficie acotada, idealmente
   clinical risks o clinical entries; no empezar por medicamentos ni ordenes.
2. Mantener el inventario `patient_scoped_route_inventory.py` sincronizado con
   cualquier ruta/superficie nueva o cambio de cobertura.
3. Mantener el gate `scripts/check-patient-scoped-read-enforcement.mjs` como
   barrera para nuevas lecturas patient-scoped sin audit ni enforcement.
4. Convertir report-only security checks en bloqueantes solo despues de baseline,
   owner, waiver y SLA revisados.
5. Mantener ABAC productivo, break-glass runtime y headers contextuales fuera de
   alcance hasta contrato especifico.

Mantener fuera de alcance PHI real, piloto clinico, receta/firma/MAR, adjuntos
productivos, consentimientos productivos, IA externa, dashboards y break-glass
runtime.

## Criterio De Producto

OneEpis debe sentirse como mesa clinica viva:

- paciente al centro
- ficha y papel como proyecciones clinicas serias
- auditoria visible
- IA local util, silenciosa y trazable
- dashboards, chat libre y modulos incompletos fuera del core

## AI-Chart

AI-Chart vive en `apps/web/src/components/clinical/ai-chart/`.

Reglas para nuevos cambios:

- mantener `patient-ai-chart-pages.tsx` como orquestador
- no agregar bloques UI inline grandes en la pagina
- preferir componentes existentes antes de crear rutas nuevas
- no sumar reglas clinicas al frontend; si una regla interpreta datos, vive en API
- todo nuevo output debe tener fuente, faltante/limite, accion humana y auditoria
- propuestas de escritura deben converger a `ClinicalPatch` revisable antes de persistir

Para foco actual y limites detallados, usar `docs/CURRENT_STATE.md` y
`docs/GOVERNANCE.md`. Este archivo no es backlog.
