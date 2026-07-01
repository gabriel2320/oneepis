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
- Sin PRs abiertos.
- Ultimos PRs cerrados: #250 refresco handoff Codex, #251 AI suggestions ABAC
  dev-only, #252 adelgazo `patient_ai.py`, #254 patient AI ABAC dev-only,
  #255 Assistant Timeline ABAC dev-only, #256 Assistant Search/Chart ABAC
  dev-only, #257 Assistant Correlation auth/audit/ABAC dev-only, #258 refresh
  de estado ABAC y #259 indice global de appointments admin/dev-only. #253
  quedo cerrado al eliminarse la rama base apilada y fue reemplazado por #254.
- Avance ABAC dev-only actual: `GET patient`, `GET record`, appointments
  patient-scoped, allergies, active problems, medications y medication drafting
  context, AI patient-scoped y Assistant Read timeline/search/chart/correlation
  detras de `ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`.
- `GET /api/v1/appointments` es indice global admin/dev-only. La UI de agenda
  global ya respeta esa frontera; las citas patient-scoped siguen siendo el
  carril clinico normal.
- `GET /api/v1/patients` ya emite `patient_index.read` minimizado. Con
  `ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`, admin/dev conservan indice global y
  roles clinicos ven solo pacientes con relacion asistencial activa. Sin
  enforcement, mantiene la navegacion visible de `/pacientes` y selectores
  clinicos.

Retomar con PRs pequenos, en este orden:

1. Auditar la experiencia UI no-demo de `/pacientes` con lista autorizada vacia
   antes de cualquier nuevo endurecimiento visible.
2. Auditar otros indices globales o pseudo-globales antes de aplicar scoping; no
   reutilizar `GlobalClinicalIndexAccessDep` salvo que el indice sea
   operacional admin/dev de verdad.
3. Mantener ABAC productivo, break-glass runtime y headers contextuales fuera de
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
