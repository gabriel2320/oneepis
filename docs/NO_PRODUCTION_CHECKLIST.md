# Checklist Versionado de No Produccion

Fecha: 2026-07-02

OneEpis no esta listo para produccion sanitaria. Este checklist convierte los
pendientes de seguridad, privacidad y gobernanza clinica en gates rastreables.

## Estado

- Repositorio publico de desarrollo temprano.
- Sin datos reales, PHI, secretos, dumps ni logs clinicos.
- Gitleaks bloquea secretos/PHI en CI.
- Gitleaks, OSV npm advisory y `pip-audit` bloquean secretos y hallazgos
  high/critical; dependency review y CodeQL siguen report-only con contrato de
  baseline, waiver y SLA antes de volverse bloqueantes.
- Rutas print patient-scoped declaran politica de auditoria explicita en el
  registry; el guard de pantallas bloquea `auditPolicy: none` en prints con
  `[patientId]`.
- ABAC patient-scoped sigue en modo dev-only amplio; no habilita PHI real,
  piloto clinico ni runtime productivo.

## Gates antes de produccion sanitaria

| ID | Gate | Estado | Criterio minimo | Evidencia actual |
| --- | --- | --- | --- | --- |
| NOPROD-SEC-001 | Gestion formal de secretos | pendiente | secretos fuera del repo, rotacion, owners y procedimiento de incidente | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/secret_management_contract.py`; `apps/api/src/oneepis_api/core/no_production_security_contract.py`; `apps/api/tests/test_secret_management_contract.py`; `apps/api/tests/test_no_production_security_contract.py`; CI `security-report` bloquea Gitleaks |
| NOPROD-SEC-002 | Cifrado en reposo | pendiente | politica de cifrado para base, backups y almacenamiento documental | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/encryption_at_rest_contract.py`; `apps/api/src/oneepis_api/core/no_production_security_contract.py`; `apps/api/tests/test_encryption_at_rest_contract.py`; `apps/api/tests/test_no_production_security_contract.py` |
| NOPROD-SEC-003 | Backups y restore | pendiente | backup automatizado, prueba de restore y RPO/RTO definidos | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/backup_restore_contract.py`; `apps/api/src/oneepis_api/core/no_production_security_contract.py`; `apps/api/tests/test_backup_restore_contract.py`; `apps/api/tests/test_no_production_security_contract.py` |
| NOPROD-SEC-004 | Retencion y eliminacion | pendiente | politica versionada de retencion, borrado, legal hold, export control y custodia documental | `docs/AUDIT.md`; `apps/api/src/oneepis_api/core/audit_retention_contract.py`; `apps/api/src/oneepis_api/core/audit_integrity_contract.py`; `apps/api/tests/test_audit_retention_contract.py`; `apps/api/tests/test_audit_integrity_contract.py` |
| NOPROD-SEC-005 | Auditoria de accesos | en progreso | lecturas auditadas en backend con actor, ruta, correlacion, dedupe, minimizacion y cobertura E2E real de filtros lectura/escritura | `docs/AUDIT.md`; `apps/api/tests/test_patient_read_audit.py`; `apps/api/tests/test_patient_audit.py`; `apps/api/tests/test_audit_snapshot.py`; `apps/api/src/oneepis_api/services/access_context_audit.py`; `apps/web/src/lib/screen-capabilities.registry.json`; `scripts/check-audit-snapshot-allowlists.mjs`; `scripts/screen-registry.mjs` |
| NOPROD-SEC-006 | Logs PHI-safe | en progreso | sanitizador backend activo, guard frontend/CI bloquea `console.*` en `apps/web/src` y contrato de observabilidad PHI-safe define logs/metricas sin PHI; faltan exportadores/dashboards productivos aprobados | `apps/api/tests/test_phi_logging.py`; `apps/api/src/oneepis_api/core/observability_contract.py`; `apps/api/tests/test_observability_contract.py`; `apps/api/src/oneepis_api/core/security_report_policy_contract.py`; `apps/api/tests/test_security_report_policy_contract.py`; `security/security-report-policy.json`; `scripts/check-frontend-phi-logs.mjs`; `scripts/check-python-advisories.mjs` |
| NOPROD-SEC-007 | Control de acceso contextual | en progreso | institucion/tenant, equipo o servicio tratante, relacion asistencial, motivo de acceso y break-glass auditado | `apps/api/src/oneepis_api/core/clinical_access.py`; `apps/api/src/oneepis_api/core/access_context_contract.py`; `apps/api/src/oneepis_api/core/access_boundary_contract.py`; `apps/api/src/oneepis_api/core/clinical_write_access_contract.py`; `apps/api/src/oneepis_api/core/patient_scoped_route_inventory.py`; `apps/api/src/oneepis_api/services/patient_access_relationship.py`; `apps/api/src/oneepis_api/services/patient_scope_enforcement.py`; `scripts/check-patient-scoped-read-enforcement.mjs`; `apps/api/tests/test_break_glass_guard.py`; `apps/api/tests/test_clinical_access_contract.py`; `apps/api/tests/test_access_context_contract.py`; `apps/api/tests/test_access_boundary_contract.py`; `apps/api/tests/test_clinical_write_access_contract.py`; `apps/api/tests/test_patient_scoped_route_inventory.py`; `apps/api/tests/test_patient_access_relationship.py`; `apps/api/tests/test_patient_abac_enforcement.py` |
| NOPROD-SEC-008 | Auth productiva | pendiente | proveedor institucional OIDC/SAML, MFA/claims de assurance, usuarios/roles persistentes, sesiones robustas, recuperacion y revocacion | `apps/api/src/oneepis_api/core/productive_auth_contract.py`; `apps/api/tests/test_auth_session_contract.py`; `apps/api/tests/test_productive_auth_contract.py`; `scripts/check-web-auth-contract.mjs` |
| NOPROD-SEC-009 | Gobernanza legal/clinica | pendiente | responsable clinico, revision legal, uso permitido y limitaciones | `docs/GOVERNANCE.md`; `apps/api/src/oneepis_api/core/clinical_governance_contract.py`; `apps/api/tests/test_clinical_governance_contract.py`; sin aprobacion operacional |
| NOPROD-SEC-010 | Politica IA externa | bloqueada | gateway PHI, anonimizacion, autorizacion, auditoria y opt-in explicito | `docs/OLLAMA_AND_TOOLS.md`; `apps/api/src/oneepis_api/core/external_ai_contract.py`; `apps/api/tests/test_external_ai_contract.py`; `apps/api/tests/test_config.py` bloquea Ollama externo fuera de desarrollo |
| NOPROD-SEC-011 | Firma/receta/orden ejecutable | bloqueada | contrato legal, permisos, folio, actor, fecha clinica y auditoria | `docs/GOVERNANCE.md`; `apps/api/tests/test_clinical_orders.py`; `apps/api/tests/test_patient_medication_catalog.py` |
| NOPROD-SEC-012 | Adjuntos y consentimientos | pendiente | almacenamiento seguro, virus scan, versionado, custodia y trazabilidad | `docs/ROADMAP.md`; `docs/SCREEN_TREE.md`; `apps/api/src/oneepis_api/core/document_custody_contract.py`; `apps/api/tests/test_document_custody_contract.py` |

## Regla de uso

- Ningun gate pendiente se resuelve con una pantalla decorativa.
- Todo cambio que cierre un gate debe incluir evidencia, tests o procedimiento
  operacional.
- Si un gate se convierte en issue GitHub, conservar el ID `NOPROD-*` en titulo
  o descripcion para trazabilidad.

## Contrato minimo ABAC futuro

Antes de cualquier piloto con PHI real, `NOPROD-SEC-007` debe quedar definido y
probado al menos con:

- Institucion o tenant clinico como frontera obligatoria de datos.
- Equipo o servicio tratante asociado al acceso.
- Relacion asistencial activa con el paciente o motivo explicito de acceso.
- Break-glass excepcional con razon, actor, fecha, correlacion y revision.
- Politica que impida acceso transversal solo por rol global.

Evidencia actual de avance sin habilitacion productiva:

- Existen stores contractuales para institucion, tenant, servicio, equipo,
  relacion paciente-equipo, membresia actor-equipo y solicitud break-glass.
- Existe resolvedor dry-run de relacion paciente/actor por equipos activos, con
  metadata minimizada para `AccessContext`.
- Existe enforcement dev-only para `GET /api/v1/patients`, `GET patient`,
  `GET record`, agenda patient-scoped, allergies, active problems, medications,
  medication drafting context, encounters, clinical entries, clinical
  events/timeline, clinical orders, clinical risks, vital signs,
  lab panels/results, patient context, AI patient-scoped, Assistant Read
  timeline/search/chart/correlation, hospital daily sheets, hospital indications
  y hospitalizaciones activas detras de
  `ONEEPIS_ABAC_ENFORCEMENT_ENABLED=true`.
- Las denegaciones emiten `access_context.denied` minimizado; las lecturas
  auditadas fuera de enforcement activo emiten decision pasiva cuando aplica.
- Existe contrato shadow de escrituras clinicas para inventario y requisitos
  pre-runtime; signos vitales, clinical risks, clinical entries,
  clinical events, clinical orders, encounters, medications, allergies, active
  problems, appointments y lab panels/results, hospital daily sheets y hospital
  indications tienen write ABAC dev-only. Ninguna escritura hereda autorizacion
  de la cobertura de lectura ni tiene runtime write ABAC productivo.
- Existe inventario ejecutable de rutas/superficies patient-scoped por metodo y
  ruta, verificado contra OpenAPI para alinear cobertura de lectura dev-only,
  superficies de escritura y checklist.
- Los snapshots de auditoria requieren allowlist explicita y las rutas API
  tienen guard contra `audit_snapshot(model)` sin fields.
- La web usa cookie `HttpOnly` + CSRF, no lee bearer desde `localStorage`, y los
  tokens firmados sin `sid` activo son rechazados con auth habilitada.
- El contrato de observabilidad PHI-safe exige `correlation_id`, logs JSON sin
  PHI, labels de metricas allowlisted y exportadores/dashboards productivos
  deshabilitados hasta aprobacion separada.
- SEC-001/002/003 tienen contrato agregado que une secretos, cifrado y
  backups/restore con sus contratos fuente, manteniendo runtime productivo y PHI
  real deshabilitados.
- Auth productiva esta definida solo como contrato OIDC/SAML/MFA/claims/sesion;
  el login local sigue siendo dev-only y no habilita usuarios productivos.
- Integridad medico-legal de auditoria queda contratada para hash-chain,
  algoritmo versionado, verificacion, legal hold y export control; nada de esto
  esta habilitado en runtime.
- Python queda con lock reproducible versionado y `check:toolchain` valida que
  las dependencias directas de `pyproject.toml` esten pinneadas.
- HIS Service Catalog v0 nombra servicios/superficies existentes sin crear
  modulos nuevos y bloquea runtime write ABAC o IA externa en el catalogo.
- Clinical Act Catalog v0 separa actos clinicos humanos de pantallas/endpoints y
  bloquea IA autonoma para esos actos.
- Screen-Service Matrix v0 exige que cada pantalla escribible del registry tenga
  servicio, backend, madurez y acto humano si escribe ficha clinica.
- AI Capability Catalog v0 cubre perfiles IA visibles y bloquea proveedor
  externo, escritura autonoma y persistencia clinica directa.
- Unit of Work piloto prueba atomicidad para un acto compuesto interno sin
  exponer API publica nueva ni habilitar firma/receta/orden ejecutable.
- Los headers contextuales siguen rechazados y auditados; `break_glass_enabled`,
  `patient_scoping_enabled` y `abac_runtime_enforced` productivo siguen en
  `False`.
- Falta enforcement runtime productivo, motivo de acceso operativo, revision
  break-glass, UI/flujo institucional, ownership clinico/legal y pruebas E2E de
  denegacion.

## Proximo paso recomendado

Mantener el gate de lectura patient-scoped por handler, el inventario OpenAPI
por metodo/ruta, la politica explicita de auditoria para prints patient-scoped
y el gate `pip-audit` high/critical. Tras PR #303, revisar/mergear el stack
#293-#303 antes de abrir nuevas superficies.
Crear issues separados a partir de estos IDs solo despues de una revision humana
del checklist. Hasta entonces, este documento es la fuente versionada.
