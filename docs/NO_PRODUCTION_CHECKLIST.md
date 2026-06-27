# Checklist Versionado de No Produccion

Fecha: 2026-06-26

OneEpis no esta listo para produccion sanitaria. Este checklist convierte los
pendientes de seguridad, privacidad y gobernanza clinica en gates rastreables.

## Estado

- Repositorio publico de desarrollo temprano.
- Sin datos reales, PHI, secretos, dumps ni logs clinicos.
- Gitleaks bloquea secretos/PHI en CI.
- Dependency review, CodeQL, OSV npm advisory check y `pip-audit` son
  report-only hasta politica explicita de bloqueo.

## Gates antes de produccion sanitaria

| ID | Gate | Estado | Criterio minimo |
| --- | --- | --- | --- |
| NOPROD-SEC-001 | Gestion formal de secretos | pendiente | secretos fuera del repo, rotacion, owners y procedimiento de incidente |
| NOPROD-SEC-002 | Cifrado en reposo | pendiente | politica de cifrado para base, backups y almacenamiento documental |
| NOPROD-SEC-003 | Backups y restore | pendiente | backup automatizado, prueba de restore y RPO/RTO definidos |
| NOPROD-SEC-004 | Retencion y eliminacion | pendiente | politica versionada de retencion, borrado y custodia documental |
| NOPROD-SEC-005 | Auditoria de accesos | en progreso | lecturas auditadas en backend (#108); falta cobertura operativa completa |
| NOPROD-SEC-006 | Logs PHI-safe | en progreso | sanitizador backend activo (#110); falta frontend/CI y revision operativa |
| NOPROD-SEC-007 | Control de acceso contextual | pendiente | institucion, equipo, relacion asistencial o motivo de acceso |
| NOPROD-SEC-008 | Auth productiva | pendiente | usuarios persistentes, hash, sesiones robustas, recuperacion y revocacion |
| NOPROD-SEC-009 | Gobernanza legal/clinica | pendiente | responsable clinico, revision legal, uso permitido y limitaciones |
| NOPROD-SEC-010 | Politica IA externa | bloqueada | gateway PHI, anonimizacion, autorizacion, auditoria y opt-in explicito |
| NOPROD-SEC-011 | Firma/receta/orden ejecutable | bloqueada | contrato legal, permisos, folio, actor, fecha clinica y auditoria |
| NOPROD-SEC-012 | Adjuntos y consentimientos | pendiente | almacenamiento seguro, virus scan, versionado, custodia y trazabilidad |

## Regla de uso

- Ningun gate pendiente se resuelve con una pantalla decorativa.
- Todo cambio que cierre un gate debe incluir evidencia, tests o procedimiento
  operacional.
- Si un gate se convierte en issue GitHub, conservar el ID `NOPROD-*` en titulo
  o descripcion para trazabilidad.

## Proximo paso recomendado

Crear issues separados a partir de estos IDs solo despues de una revision humana
del checklist. Hasta entonces, este documento es la fuente versionada.
