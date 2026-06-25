# Read Access Policy - OneEpis

Generado: 2026-06-25T01:27:44.002Z

## Resumen

- Rutas revisadas: 26
- Auditoria requerida P0: 6
- Auditoria requerida P1: 15
- Requieren politica de volumen/retencion: 2
- Exentas tecnicas: 3
- Listo para bloqueo CI: no

## Bloqueantes antes de activar CI

- definir retencion y volumen esperado de eventos de lectura
- evitar auditoria de endpoints tecnicos o polling frecuente
- definir si busquedas/listas se auditan siempre, por muestreo o por acceso a ficha
- definir estructura de evento sin duplicar datos clinicos sensibles en metadata
- agregar tests de no regresion antes de activar bloqueo CI

## Campos minimos futuros

- actor_id
- actor_roles
- request_method
- request_path
- correlation_id
- patient_id cuando exista
- resource_type
- resource_id cuando exista
- access_policy
- created_at

## Matriz

Ruta | Sensibilidad | Politica propuesta | Fase | CI | Razon
--- | --- | --- | --- | --- | ---
GET /api/v1/ai/status (apps/api/src/oneepis_api/api/v1/routes/ai.py) | tecnica_o_sesion | EXEMPT_TECHNICAL | no_aplica | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/auth/me (apps/api/src/oneepis_api/api/v1/routes/auth.py) | tecnica_o_sesion | EXEMPT_TECHNICAL | no_aplica | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/health (apps/api/src/oneepis_api/api/v1/routes/health.py) | tecnica_o_sesion | EXEMPT_TECHNICAL | no_aplica | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/hospitalization/beds (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | clinical_read | REVIEW_VOLUME_POLICY | diseno_retencion | report-only | Puede generar alto volumen o corresponder a catalogo/lista; requiere politica de muestreo o retencion.
GET /api/v1/hospitalization/active (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | hospital_board | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/hospitalization/patients/{patient_id}/daily-sheets (apps/api/src/oneepis_api/api/v1/routes/hospitalization_daily_sheets.py) | hospital_document | AUDIT_REQUIRED_P0 | primera_implementacion | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/hospitalization/patients/{patient_id}/indications (apps/api/src/oneepis_api/api/v1/routes/hospitalization_indications.py) | hospital_document | AUDIT_REQUIRED_P0 | primera_implementacion | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/allergies (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/allergies/{allergy_id} (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/assistant/timeline (apps/api/src/oneepis_api/api/v1/routes/patient_assistant.py) | clinical_timeline | AUDIT_REQUIRED_P0 | primera_implementacion | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/audit-events (apps/api/src/oneepis_api/api/v1/routes/patient_audit.py) | audit_trail | AUDIT_REQUIRED_P0 | primera_implementacion | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | patient_search_or_identity | REVIEW_VOLUME_POLICY | diseno_retencion | report-only | Puede generar alto volumen o corresponder a catalogo/lista; requiere politica de muestreo o retencion.
GET /api/v1/patients/{patient_id} (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/record (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | patient_record | AUDIT_REQUIRED_P0 | primera_implementacion | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/encounters (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/encounters/{encounter_id} (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-entries (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-entries/{entry_id} (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-events (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/timeline (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | clinical_timeline | AUDIT_REQUIRED_P0 | primera_implementacion | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/medications (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/medications/{medication_id} (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/problems (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/problems/{problem_id} (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/vital-signs (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/vital-signs/{vital_sign_id} (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
