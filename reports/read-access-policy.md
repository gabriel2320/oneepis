# Read Access Policy - OneEpis

Generado: 2026-06-25T02:11:14.874Z

## Resumen

- Rutas revisadas: 39
- Auditoria requerida P0: 6
- Auditoria requerida P1: 25
- Requieren politica de volumen/retencion: 3
- Exentas tecnicas: 5
- Alto volumen probable: 4
- Retencion estricta candidata: 6
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

Ruta | Sensibilidad | Politica propuesta | Fase | Volumen | Retencion candidata | CI | Razon
--- | --- | --- | --- | --- | --- | --- | ---
GET /api/v1/ai/status (apps/api/src/oneepis_api/api/v1/routes/ai.py) | tecnica_o_sesion | EXEMPT_TECHNICAL | no_aplica | technical | none | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/appointments (apps/api/src/oneepis_api/api/v1/routes/appointments.py) | clinical_read | REVIEW_VOLUME_POLICY | diseno_retencion | high_frequency | sample_or_short_access_trail | report-only | Puede generar alto volumen o corresponder a catalogo/lista; requiere politica de muestreo o retencion.
GET /api/v1/patients/{patient_id}/appointments (apps/api/src/oneepis_api/api/v1/routes/appointments.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/appointments/{appointment_id} (apps/api/src/oneepis_api/api/v1/routes/appointments.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/auth/me (apps/api/src/oneepis_api/api/v1/routes/auth.py) | tecnica_o_sesion | EXEMPT_TECHNICAL | no_aplica | technical | none | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/health (apps/api/src/oneepis_api/api/v1/routes/health.py) | tecnica_o_sesion | EXEMPT_TECHNICAL | no_aplica | technical | none | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/hospitalization/beds (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | clinical_read | REVIEW_VOLUME_POLICY | diseno_retencion | high_frequency | sample_or_short_access_trail | report-only | Puede generar alto volumen o corresponder a catalogo/lista; requiere politica de muestreo o retencion.
GET /api/v1/hospitalization/active (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | hospital_board | AUDIT_REQUIRED_P1 | segunda_implementacion | high_frequency | sample_or_short_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/hospitalization/patients/{patient_id}/daily-sheets (apps/api/src/oneepis_api/api/v1/routes/hospitalization_daily_sheets.py) | hospital_document | AUDIT_REQUIRED_P0 | primera_implementacion | interactive_sensitive | strict_access_trail | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/hospitalization/patients/{patient_id}/indications (apps/api/src/oneepis_api/api/v1/routes/hospitalization_indications.py) | hospital_document | AUDIT_REQUIRED_P0 | primera_implementacion | interactive_sensitive | strict_access_trail | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/medication-catalog (apps/api/src/oneepis_api/api/v1/routes/medication_catalog.py) | no_clinica_detectada | EXEMPT_TECHNICAL | no_aplica | technical | none | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/medication-catalog/{catalog_item_id} (apps/api/src/oneepis_api/api/v1/routes/medication_catalog.py) | no_clinica_detectada | EXEMPT_TECHNICAL | no_aplica | technical | none | report-only | Ruta tecnica, health, sesion o estado operacional sin lectura clinica de paciente.
GET /api/v1/patients/{patient_id}/allergies (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/allergies/{allergy_id} (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/assistant/search (apps/api/src/oneepis_api/api/v1/routes/patient_assistant_search.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/assistant/timeline (apps/api/src/oneepis_api/api/v1/routes/patient_assistant_timeline.py) | clinical_timeline | AUDIT_REQUIRED_P0 | primera_implementacion | interactive_sensitive | strict_access_trail | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/audit-events (apps/api/src/oneepis_api/api/v1/routes/patient_audit.py) | audit_trail | AUDIT_REQUIRED_P0 | primera_implementacion | interactive_sensitive | strict_access_trail | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/clinical-risks (apps/api/src/oneepis_api/api/v1/routes/patient_clinical_risks.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-risks/{risk_id} (apps/api/src/oneepis_api/api/v1/routes/patient_clinical_risks.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | patient_search_or_identity | REVIEW_VOLUME_POLICY | diseno_retencion | high_frequency | sample_or_short_access_trail | report-only | Puede generar alto volumen o corresponder a catalogo/lista; requiere politica de muestreo o retencion.
GET /api/v1/patients/{patient_id} (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/record (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | patient_record | AUDIT_REQUIRED_P0 | primera_implementacion | interactive_sensitive | strict_access_trail | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/encounters (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/encounters/{encounter_id} (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-entries (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-entries/{entry_id} (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-events (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/clinical-events/{event_id} (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/timeline (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | clinical_timeline | AUDIT_REQUIRED_P0 | primera_implementacion | interactive_sensitive | strict_access_trail | report-only | Lectura clinica sensible o documental; debe dejar trail antes de produccion.
GET /api/v1/patients/{patient_id}/lab-panels (apps/api/src/oneepis_api/api/v1/routes/patient_lab_panels.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/lab-panels/{panel_id} (apps/api/src/oneepis_api/api/v1/routes/patient_lab_panels.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/lab-panels/{panel_id}/results/{result_id} (apps/api/src/oneepis_api/api/v1/routes/patient_lab_panels.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/medications (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/medication-drafting-context (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/medications/{medication_id} (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/problems (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/problems/{problem_id} (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/vital-signs (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
GET /api/v1/patients/{patient_id}/vital-signs/{vital_sign_id} (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | patient_child_entity | AUDIT_REQUIRED_P1 | segunda_implementacion | interactive_clinical | standard_access_trail | report-only | Lectura clinica de entidad o tablero con paciente; auditable tras validar volumen.
