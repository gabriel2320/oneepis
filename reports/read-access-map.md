# Read Access Map - OneEpis

Generado: 2026-06-25T01:27:43.996Z

## Resumen

- Rutas GET revisadas: 26
- Candidatas a auditoria de lectura: 23
- Exenciones tecnicas/sesion: 3
- Brechas report-only: 23

## Politica

Este reporte no bloquea CI. C5-01 solo clasifica rutas de lectura sensibles para disenar auditoria de acceso antes de escribir eventos nuevos.

## Matriz

Ruta | Funcion | Politica | Sensibilidad | Acceso | Auditoria lectura actual | Recomendacion
--- | --- | --- | --- | --- | --- | ---
GET /api/v1/ai/status (apps/api/src/oneepis_api/api/v1/routes/ai.py) | get_ai_status | EXEMPT_TECHNICAL | tecnica_o_sesion | no requerida | no requerida | Mantener fuera de auditoria clinica de lectura.
GET /api/v1/auth/me (apps/api/src/oneepis_api/api/v1/routes/auth.py) | get_me | EXEMPT_TECHNICAL | tecnica_o_sesion | CurrentUserDep | no requerida | Mantener fuera de auditoria clinica de lectura.
GET /api/v1/health (apps/api/src/oneepis_api/api/v1/routes/health.py) | health | EXEMPT_TECHNICAL | tecnica_o_sesion | no requerida | no requerida | Mantener fuera de auditoria clinica de lectura.
GET /api/v1/hospitalization/beds (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | list_hospital_beds | READ_AUDIT_CANDIDATE | clinical_read | router:require_patient_read_access | no implementada | Revisar manualmente; parece lectura clinica por modelo o schema.
GET /api/v1/hospitalization/active (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | list_active_hospitalizations | READ_AUDIT_CANDIDATE | hospital_board | router:require_patient_read_access | no implementada | Auditar si expone pacientes hospitalizados; revisar volumen antes de bloquear.
GET /api/v1/hospitalization/patients/{patient_id}/daily-sheets (apps/api/src/oneepis_api/api/v1/routes/hospitalization_daily_sheets.py) | list_hospital_daily_sheets | READ_AUDIT_CANDIDATE | hospital_document | router:require_patient_read_access | no implementada | Auditar como lectura de documento o lista clinica hospitalaria.
GET /api/v1/hospitalization/patients/{patient_id}/indications (apps/api/src/oneepis_api/api/v1/routes/hospitalization_indications.py) | list_hospital_indications | READ_AUDIT_CANDIDATE | hospital_document | router:require_patient_read_access | no implementada | Auditar como lectura de documento o lista clinica hospitalaria.
GET /api/v1/patients/{patient_id}/allergies (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | list_allergies | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/allergies/{allergy_id} (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | get_allergy | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/assistant/timeline (apps/api/src/oneepis_api/api/v1/routes/patient_assistant.py) | get_assistant_timeline | READ_AUDIT_CANDIDATE | clinical_timeline | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura longitudinal sensible.
GET /api/v1/patients/{patient_id}/audit-events (apps/api/src/oneepis_api/api/v1/routes/patient_audit.py) | list_patient_audit_events | READ_AUDIT_CANDIDATE | audit_trail | router:PATIENT_ROUTER_OPTIONS | no implementada | Prioridad alta: lectura de auditoria clinica debe dejar trail.
GET /api/v1/patients (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | list_patients | READ_AUDIT_CANDIDATE | patient_search_or_identity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar o muestrear segun volumen: expone identidad/lista de pacientes.
GET /api/v1/patients/{patient_id} (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | get_patient | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/record (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | get_patient_record | READ_AUDIT_CANDIDATE | patient_record | router:PATIENT_ROUTER_OPTIONS | no implementada | Prioridad alta: lectura de ficha longitudinal debe auditarse.
GET /api/v1/patients/{patient_id}/encounters (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | list_clinical_encounters | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/encounters/{encounter_id} (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | get_clinical_encounter | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/clinical-entries (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | list_clinical_entries | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/clinical-entries/{entry_id} (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | get_clinical_entry | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/clinical-events (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | list_clinical_events | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/timeline (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | get_clinical_timeline | READ_AUDIT_CANDIDATE | clinical_timeline | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura longitudinal sensible.
GET /api/v1/patients/{patient_id}/medications (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | list_medications | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/medications/{medication_id} (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | get_medication | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/problems (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | list_active_problems | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/problems/{problem_id} (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | get_active_problem | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/vital-signs (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | list_vital_signs | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
GET /api/v1/patients/{patient_id}/vital-signs/{vital_sign_id} (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | get_vital_sign | READ_AUDIT_CANDIDATE | patient_child_entity | router:PATIENT_ROUTER_OPTIONS | no implementada | Auditar como lectura de entidad clinica asociada a paciente.
