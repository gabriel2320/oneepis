# Checklist Versionado de No Produccion

Fecha: 2026-06-29

OneEpis no esta listo para produccion sanitaria. Este checklist convierte los
pendientes de seguridad, privacidad y gobernanza clinica en gates rastreables.

## Estado

- Repositorio publico de desarrollo temprano.
- Sin datos reales, PHI, secretos, dumps ni logs clinicos.
- Gitleaks bloquea secretos/PHI en CI.
- OSV npm advisory check bloquea hallazgos high/critical; dependency review,
  CodeQL y `pip-audit` siguen report-only hasta politica explicita.

## Gates antes de produccion sanitaria

| ID | Gate | Estado | Criterio minimo | Evidencia actual |
| --- | --- | --- | --- | --- |
| NOPROD-SEC-001 | Gestion formal de secretos | pendiente | secretos fuera del repo, rotacion, owners y procedimiento de incidente | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/secret_management_contract.py`; `apps/api/tests/test_secret_management_contract.py`; CI `security-report` bloquea Gitleaks |
| NOPROD-SEC-002 | Cifrado en reposo | pendiente | politica de cifrado para base, backups y almacenamiento documental | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/encryption_at_rest_contract.py`; `apps/api/tests/test_encryption_at_rest_contract.py` |
| NOPROD-SEC-003 | Backups y restore | pendiente | backup automatizado, prueba de restore y RPO/RTO definidos | `docs/SECURITY_PRIVACY.md`; `apps/api/src/oneepis_api/core/backup_restore_contract.py`; `apps/api/tests/test_backup_restore_contract.py` |
| NOPROD-SEC-004 | Retencion y eliminacion | pendiente | politica versionada de retencion, borrado y custodia documental | `docs/AUDIT.md`; `apps/api/src/oneepis_api/core/audit_retention_contract.py`; `apps/api/tests/test_audit_retention_contract.py` |
| NOPROD-SEC-005 | Auditoria de accesos | en progreso | lecturas auditadas en backend con actor, ruta, correlacion, dedupe y cobertura E2E real de filtros lectura/escritura | `apps/api/tests/test_patient_read_audit.py`; `apps/api/tests/test_patient_audit.py` |
| NOPROD-SEC-006 | Logs PHI-safe | en progreso | sanitizador backend activo y guard frontend/CI bloquea `console.*` en `apps/web/src`; falta observabilidad productiva formal | `apps/api/tests/test_phi_logging.py`; `scripts/check-frontend-phi-logs.mjs` |
| NOPROD-SEC-007 | Control de acceso contextual | pendiente | institucion/tenant, equipo o servicio tratante, relacion asistencial, motivo de acceso y break-glass auditado | `apps/api/src/oneepis_api/core/clinical_access.py`; `apps/api/tests/test_break_glass_guard.py`; `apps/api/tests/test_clinical_access_contract.py` |
| NOPROD-SEC-008 | Auth productiva | pendiente | usuarios persistentes, hash, sesiones robustas, recuperacion y revocacion | `apps/api/src/oneepis_api/core/productive_auth_contract.py`; `apps/api/tests/test_auth_session_contract.py`; `apps/api/tests/test_productive_auth_contract.py` |
| NOPROD-SEC-009 | Gobernanza legal/clinica | pendiente | responsable clinico, revision legal, uso permitido y limitaciones | `docs/GOVERNANCE.md`; sin aprobacion operacional |
| NOPROD-SEC-010 | Politica IA externa | bloqueada | gateway PHI, anonimizacion, autorizacion, auditoria y opt-in explicito | `docs/OLLAMA_AND_TOOLS.md`; `apps/api/tests/test_config.py` bloquea Ollama externo fuera de desarrollo |
| NOPROD-SEC-011 | Firma/receta/orden ejecutable | bloqueada | contrato legal, permisos, folio, actor, fecha clinica y auditoria | `docs/GOVERNANCE.md`; `apps/api/tests/test_clinical_orders.py`; `apps/api/tests/test_patient_medication_catalog.py` |
| NOPROD-SEC-012 | Adjuntos y consentimientos | pendiente | almacenamiento seguro, virus scan, versionado, custodia y trazabilidad | `docs/ROADMAP.md`; `docs/SCREEN_TREE.md`; sin almacenamiento documental productivo |

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

## Proximo paso recomendado

Crear issues separados a partir de estos IDs solo despues de una revision humana
del checklist. Hasta entonces, este documento es la fuente versionada.
