# Current State

Fecha: 2026-07-01

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
- Auditoria de lectura/escritura patient-scoped existe con actor, ruta,
  `correlation_id`, minimizacion por allowlists y eventos de denegacion.
- Logs PHI-safe backend y guard frontend contra `console.*` estan activos en
  checks. No hay observabilidad productiva formal.
- `security-report` bloquea Gitleaks y OSV npm high/critical. Dependency
  review, CodeQL y `pip-audit` siguen report-only hasta baseline/waiver/SLA.
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
- `encounters`

El resto de escrituras sigue sin write ABAC. Ninguna escritura tiene ABAC
runtime productivo, motivo operacional de acceso ni break-glass runtime.

## Fuentes Ejecutables

- Rutas/superficies patient-scoped: `apps/api/src/oneepis_api/core/patient_scoped_route_inventory.py`.
- Contrato shadow de escrituras: `apps/api/src/oneepis_api/core/clinical_write_access_contract.py`.
- Registry visible de pantallas: `apps/web/src/lib/screen-capabilities.registry.json`.
- Tabla generada de rutas: `docs/SCREEN_TREE.md`.
- Checklist versionado no-produccion: `docs/NO_PRODUCTION_CHECKLIST.md`.

## Riesgos Vivos

- No produccion sanitaria, no piloto con PHI, no software clinico certificado.
- Faltan secretos formales, cifrado, backups/restore, retencion, identidad
  productiva, observabilidad PHI-safe formal y governance clinico/legal.
- ABAC productivo requiere institucion/tenant, equipo/servicio tratante,
  relacion asistencial, motivo de acceso y break-glass revisable.
- Auditoria medico-legal completa sigue pendiente: retencion, exportacion,
  revision e inmutabilidad formal.
- IA externa bloqueada hasta gateway PHI, anonimizacion, autorizacion, auditoria
  y opt-in explicito.

## Proximo Objetivo

No ampliar modulos clinicos. El siguiente trabajo debe reducir riesgo
operacional o consolidar contrato. Prioridad actual: continuar write ABAC
dev-only por superficies acotadas, con `clinical_events` como siguiente
candidato natural; no empezar por medicamentos ni ordenes.

## Regla Documental

Al cerrar cada PR que cambie plan, avance, estado, seguridad o no-produccion,
sincronizar juntos los documentos vivos afectados:

- `docs/CURRENT_STATE.md`
- `docs/CODEX_PLAN.md`
- `docs/NO_PRODUCTION_CHECKLIST.md`
- `docs/SCREEN_TREE.md` solo si cambia ruta/pantalla/registry
- doc de dominio solo si cambia una regla de ese dominio

No crear snapshots nuevos ni duplicar listas de estado en documentos de vision.
