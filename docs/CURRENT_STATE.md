# Current State

Fecha: 2026-07-02

Este documento es la verdad operativa vigente. No es historial ni changelog.
El historial cronologico vive en `docs/ROADMAP.md`; el handoff para agentes vive
en `docs/CODEX_PLAN.md`.

## Producto Actual

- OneEpis es una ficha clinica longitudinal pre-HIS, no un HIS completo.
- Entrada principal: login local de desarrollo, `/home` como mapa fisico,
  `/consulta` para ambulatorio, `/hospitalizacion` para hospitalizacion minima y
  `/pacientes/[patientId]/ficha` como centro longitudinal.
- La identidad clinica sigue siendo `Patient`; `ClinicalEncounter` separa
  contexto ambulatorio/hospitalario; timeline, ficha y papel reconcilian eventos,
  evoluciones, medicacion, alergias, problemas, riesgos, signos y resultados.
- Ambulatorio minimo existe: agenda persistida, preconsulta minima, atencion,
  resumen de lectura y ficha comun.
- Hospitalizacion minima existe: camas, rondas, ingreso borrador, hoja diaria,
  indicaciones borrador y epicrisis borrador.
- Documentos/papel existen como proyecciones carta con metadata visible. Firma
  real, receta valida, MAR, consentimientos y adjuntos productivos siguen
  bloqueados.
- AI-Chart/Assistant Read es apoyo contextual gobernado: resume y propone
  borradores revisables; no decide, no firma y no escribe sin confirmacion
  humana/backend.

## Seguridad Y Auditoria

- Auth local y RBAC minimo sirven solo para desarrollo.
- La web usa cookie `HttpOnly` y CSRF; `localStorage` solo conserva un marcador
  no sensible de sesion y limpia la clave bearer legacy.
- Con auth habilitada, los tokens firmados sin `sid` server-side activo son
  rechazados.
- Auditoria de lectura/escritura patient-scoped existe con actor, ruta,
  `correlation_id`, minimizacion por allowlists y eventos de denegacion.
- `audit_snapshot` exige allowlist explicita y las rutas API tienen guard contra
  snapshots clinicos completos por accidente.
- Las rutas print patient-scoped declaran `read_audit` en el registry; el guard
  de pantallas falla si un print con `[patientId]` queda con `auditPolicy: none`.
- Logs PHI-safe backend, guard frontend contra `console.*` y contrato formal de
  observabilidad PHI-safe estan activos. No hay exportadores ni dashboards
  productivos.
- `security-report` bloquea Gitleaks, OSV npm high/critical y `pip-audit`
  high/critical. Dependency review y CodeQL siguen report-only con baseline,
  owner y waiver versionados hasta SLA de bloqueo.
- `GET /api/v1/appointments` es indice global admin/dev-only; agenda
  patient-scoped sigue como carril clinico normal.

## ABAC Dev-Only

Detras de `ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`, `main` tiene read ABAC
dev-only para:

- `GET /api/v1/patients`, `GET patient`, `GET record`.
- Appointments patient-scoped.
- Allergies, active problems, medications y medication drafting context.
- Encounters, clinical entries, clinical events/timeline, clinical orders,
  clinical risks, vital signs, lab panels/results y patient context.
- AI patient-scoped y Assistant Read timeline/search/chart/correlation.
- Hospital daily sheets, hospital indications y hospitalizaciones activas.

Esto no habilita PHI real ni ABAC productivo. `patient_scoping_enabled`,
`abac_runtime_enforced` y `break_glass_enabled` productivos siguen en `False`.

## Write ABAC Dev-Only

Las escrituras clinicas tienen contrato shadow de inventario y requisitos.
Superficies con write ABAC dev-only:

- `vital_signs`
- `clinical_risks`
- `clinical_entries`
- `clinical_events`
- `clinical_orders`
- `encounters`
- `medications`
- `allergies`
- `active_problems`
- `appointments`
- `lab_panels_results`
- `hospital_daily_sheets`
- `hospital_indications`

Todas las superficies del contrato shadow tienen write ABAC dev-only. Ninguna
escritura tiene ABAC runtime productivo, motivo operacional de acceso,
break-glass runtime, firma, receta valida ni orden ejecutable.

## Fuentes Ejecutables

- Rutas/superficies patient-scoped por metodo/ruta:
  `apps/api/src/oneepis_api/core/patient_scoped_route_inventory.py`, verificado
  contra OpenAPI por `npm run check:patient-route-inventory`.
- Contrato shadow de escrituras: `apps/api/src/oneepis_api/core/clinical_write_access_contract.py`.
- Registry visible de pantallas: `apps/web/src/lib/screen-capabilities.registry.json`.
- Tabla generada de rutas: `docs/SCREEN_TREE.md`.
- Baseline/waivers de security-report: `security/security-report-policy.json`.
- Contrato PHI-safe de observabilidad: `apps/api/src/oneepis_api/core/observability_contract.py`.
- Contrato agregado SEC-001/002/003:
  `apps/api/src/oneepis_api/core/no_production_security_contract.py`.
- Contrato auth productiva docs-only:
  `apps/api/src/oneepis_api/core/productive_auth_contract.py`.
- Checklist versionado no-produccion: `docs/NO_PRODUCTION_CHECKLIST.md`.

## Riesgos Vivos

- No produccion sanitaria, no piloto con PHI, no software clinico certificado.
- Faltan secretos formales, cifrado, backups/restore, retencion, identidad
  productiva, integracion productiva de observabilidad PHI-safe y governance
  clinico/legal.
- ABAC productivo requiere institucion/tenant, equipo/servicio tratante,
  relacion asistencial, motivo de acceso y break-glass revisable.
- Auditoria medico-legal completa sigue pendiente: retencion, exportacion,
  revision e inmutabilidad formal.
- IA externa bloqueada hasta gateway PHI, anonimizacion, autorizacion, auditoria
  y opt-in explicito.

## Proximo Objetivo

No ampliar modulos clinicos. El ultimo PR GitHub confirmado sigue siendo #292;
los commits directos post-#292 no consumen numeracion de PR. PR #293 corresponde
a security report fase 2, PR #294 a observabilidad PHI-safe formal, PR #295 a
contratos SEC-001/002/003 y PR #296 a auth productiva docs-only. El siguiente
trabajo debe seguir la cola post-#296 en reduccion de riesgo operacional:

- PR #297: integridad medico-legal de auditoria como contrato.
- PR #298: reproducibilidad Python.
- PR #299: HIS Service Catalog v0.
- PR #300: Clinical Act Catalog v0.
- PR #301: Screen-Service Matrix.
- PR #302: AI Capability Catalog.
- PR #303: Unit of Work para un acto clinico compuesto.

No avanzar a runtime write ABAC, break-glass runtime, firma, receta valida,
orden ejecutable, PHI real ni IA externa.

## Regla Documental

Al cerrar cada PR que cambie plan, avance, estado, seguridad o no-produccion,
sincronizar juntos los documentos vivos afectados:

- `docs/CURRENT_STATE.md`
- `docs/CODEX_PLAN.md`
- `docs/NO_PRODUCTION_CHECKLIST.md`
- `docs/SCREEN_TREE.md` solo si cambia ruta/pantalla/registry
- doc de dominio solo si cambia una regla de ese dominio

No crear snapshots nuevos ni duplicar listas de estado en documentos de vision.
