# Checklist Versionado de No Produccion

Fecha: 2026-07-01

OneEpis no esta listo para produccion sanitaria. Este checklist convierte los
pendientes de seguridad, privacidad y gobernanza clinica en gates rastreables.

## Estado

- Repositorio publico de desarrollo temprano.
- Sin datos reales, PHI, secretos, dumps ni logs clinicos.
- Gitleaks bloquea secretos/PHI en CI.
- Gitleaks y OSV npm advisory bloquean secretos y hallazgos npm
  high/critical; dependency review, CodeQL y `pip-audit` siguen report-only con
  contrato de baseline, waiver y SLA antes de volverse bloqueantes.
- ABAC patient-scoped sigue en modo dev-only y parcial; no habilita PHI real,
  piloto clinico ni runtime productivo.

## Gates antes de produccion sanitaria

| ID | Gate | Estado | Criterio minimo | Evidencia actual |
| --- | --- | --- | --- | --- |
| NOPROD-SEC-001 | Gestion formal de secretos | pendiente | secretos fuera del repo, rotacion, owners y procedimiento de incidente | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/secret_management_contract.py`; `apps/api/tests/test_secret_management_contract.py`; CI `security-report` bloquea Gitleaks |
| NOPROD-SEC-002 | Cifrado en reposo | pendiente | politica de cifrado para base, backups y almacenamiento documental | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/encryption_at_rest_contract.py`; `apps/api/tests/test_encryption_at_rest_contract.py` |
| NOPROD-SEC-003 | Backups y restore | pendiente | backup automatizado, prueba de restore y RPO/RTO definidos | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/backup_restore_contract.py`; `apps/api/tests/test_backup_restore_contract.py` |
| NOPROD-SEC-004 | Retencion y eliminacion | pendiente | politica versionada de retencion, borrado y custodia documental | `docs/AUDIT.md`; `apps/api/src/oneepis_api/core/audit_retention_contract.py`; `apps/api/src/oneepis_api/core/audit_integrity_contract.py`; `apps/api/tests/test_audit_retention_contract.py`; `apps/api/tests/test_audit_integrity_contract.py` |
| NOPROD-SEC-005 | Auditoria de accesos | en progreso | lecturas auditadas en backend con actor, ruta, correlacion, dedupe, minimizacion y cobertura E2E real de filtros lectura/escritura | `docs/AUDIT.md`; `apps/api/tests/test_patient_read_audit.py`; `apps/api/tests/test_patient_audit.py`; `apps/api/src/oneepis_api/services/access_context_audit.py` |
| NOPROD-SEC-006 | Logs PHI-safe | en progreso | sanitizador backend activo y guard frontend/CI bloquea `console.*` en `apps/web/src`; falta observabilidad productiva formal | `apps/api/tests/test_phi_logging.py`; `apps/api/src/oneepis_api/core/security_report_policy_contract.py`; `apps/api/tests/test_security_report_policy_contract.py`; `scripts/check-frontend-phi-logs.mjs` |
| NOPROD-SEC-007 | Control de acceso contextual | en progreso | institucion/tenant, equipo o servicio tratante, relacion asistencial, motivo de acceso y break-glass auditado | `apps/api/src/oneepis_api/core/clinical_access.py`; `apps/api/src/oneepis_api/core/access_context_contract.py`; `apps/api/src/oneepis_api/core/access_boundary_contract.py`; `apps/api/src/oneepis_api/core/clinical_write_access_contract.py`; `apps/api/src/oneepis_api/core/patient_scoped_route_inventory.py`; `apps/api/src/oneepis_api/services/patient_access_relationship.py`; `apps/api/src/oneepis_api/services/patient_scope_enforcement.py`; `scripts/check-patient-scoped-read-enforcement.mjs`; `apps/api/tests/test_break_glass_guard.py`; `apps/api/tests/test_clinical_access_contract.py`; `apps/api/tests/test_access_context_contract.py`; `apps/api/tests/test_access_boundary_contract.py`; `apps/api/tests/test_clinical_write_access_contract.py`; `apps/api/tests/test_patient_scoped_route_inventory.py`; `apps/api/tests/test_patient_access_relationship.py`; `apps/api/tests/test_patient_abac_enforcement.py` |
| NOPROD-SEC-008 | Auth productiva | pendiente | proveedor institucional, MFA, usuarios/roles persistentes, sesiones robustas, recuperacion y revocacion | `apps/api/src/oneepis_api/core/productive_auth_contract.py`; `apps/api/tests/test_auth_session_contract.py`; `apps/api/tests/test_productive_auth_contract.py` |
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
  clinical events y encounters tienen write ABAC dev-only, las demas escrituras
  siguen sin write ABAC y ninguna hereda autorizacion de la cobertura de
  lectura.
- Existe inventario ejecutable de rutas/superficies patient-scoped para alinear
  cobertura de lectura dev-only, superficies de escritura y checklist.
- Los headers contextuales siguen rechazados y auditados; `break_glass_enabled`,
  `patient_scoping_enabled` y `abac_runtime_enforced` productivo siguen en
  `False`.
- Falta enforcement runtime productivo, motivo de acceso operativo, revision
  break-glass, UI/flujo institucional, ownership clinico/legal y pruebas E2E de
  denegacion.

## Proximo paso recomendado

Mantener el gate de lectura patient-scoped por handler y usar el contrato shadow
de escrituras clinicas como frontera pre-runtime sin habilitar ABAC productivo.
Crear issues separados a partir de estos IDs solo despues de una revision humana
del checklist. Hasta entonces, este documento es la fuente versionada.
