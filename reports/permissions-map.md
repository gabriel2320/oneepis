# Permissions Map - OneEpis

Generado: 2026-06-25T01:05:06.976Z

## Resumen

- Rutas mutantes clinicas revisadas: 35
- Brechas criticas: 0
- Advertencias: 0

## Matriz

Ruta | Funcion | Actor/permiso | Auditoria | Test 403 | Brechas criticas | Advertencias
--- | --- | --- | --- | --- | --- | ---
POST /beds (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | create_hospital_bed | EncounterActorDep | record_audit_event | apps/api/tests/test_hospital_beds.py | OK | OK
PATCH /beds/{bed_id} (apps/api/src/oneepis_api/api/v1/routes/hospitalization.py) | update_hospital_bed | EncounterActorDep | record_audit_event | apps/api/tests/test_hospital_beds.py | OK | OK
POST /patients/{patient_id}/daily-sheets (apps/api/src/oneepis_api/api/v1/routes/hospitalization_daily_sheets.py) | create_hospital_daily_sheet | HospitalDailySheetActorDep | record_audit_event | apps/api/tests/test_hospital_daily_sheets.py | OK | OK
PATCH /patients/{patient_id}/daily-sheets/{sheet_id} (apps/api/src/oneepis_api/api/v1/routes/hospitalization_daily_sheets.py) | update_hospital_daily_sheet | HospitalDailySheetActorDep | record_audit_event | apps/api/tests/test_hospital_daily_sheets.py | OK | OK
POST /patients/{patient_id}/indications (apps/api/src/oneepis_api/api/v1/routes/hospitalization_indications.py) | create_hospital_indication | HospitalIndicationActorDep | record_audit_event | apps/api/tests/test_hospital_indications.py | OK | OK
PATCH /patients/{patient_id}/indications/{indication_id} (apps/api/src/oneepis_api/api/v1/routes/hospitalization_indications.py) | update_hospital_indication | HospitalIndicationActorDep | record_audit_event | apps/api/tests/test_hospital_indications.py | OK | OK
POST /{patient_id}/ai/draft-soap-from-events (apps/api/src/oneepis_api/api/v1/routes/patient_ai.py) | create_draft_soap_from_events | AiAccessDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/ai/event-proposals-from-entry (apps/api/src/oneepis_api/api/v1/routes/patient_ai.py) | create_event_proposals_from_entry | AiAccessDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/ai/confirm-clinical-patch (apps/api/src/oneepis_api/api/v1/routes/patient_ai.py) | confirm_clinical_patch | AiAccessDep | delegated:confirm_patch_service | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/ai/clinical-intent (apps/api/src/oneepis_api/api/v1/routes/patient_ai.py) | create_clinical_intent | AiAccessDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/ai/clinical-intent-route (apps/api/src/oneepis_api/api/v1/routes/patient_ai.py) | route_patient_clinical_intent | AiAccessDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/ai/action-decision (apps/api/src/oneepis_api/api/v1/routes/patient_ai.py) | decide_clinical_intent_action | AiAccessDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/ai/review-item-decision (apps/api/src/oneepis_api/api/v1/routes/patient_ai.py) | decide_clinical_review_item | AiAccessDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/allergies (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | create_allergy | AllergyActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id}/allergies/{allergy_id} (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | update_allergy | AllergyActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
DELETE /{patient_id}/allergies/{allergy_id} (apps/api/src/oneepis_api/api/v1/routes/patient_allergies.py) | delete_allergy | AllergyActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST  (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | create_patient | PatientActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id} (apps/api/src/oneepis_api/api/v1/routes/patient_core.py) | update_patient | PatientActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/encounters (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | create_clinical_encounter | EncounterActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id}/encounters/{encounter_id} (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | update_clinical_encounter | EncounterActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
DELETE /{patient_id}/encounters/{encounter_id} (apps/api/src/oneepis_api/api/v1/routes/patient_encounters.py) | cancel_clinical_encounter | EncounterActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/clinical-entries (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | create_clinical_entry | ClinicalEntryActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id}/clinical-entries/{entry_id} (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | update_clinical_entry | ClinicalEntryActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
DELETE /{patient_id}/clinical-entries/{entry_id} (apps/api/src/oneepis_api/api/v1/routes/patient_entries.py) | delete_draft_clinical_entry | ClinicalEntryActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/clinical-events (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | create_clinical_event | ClinicalEventActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id}/clinical-events/{event_id} (apps/api/src/oneepis_api/api/v1/routes/patient_events.py) | update_clinical_event | ClinicalEventActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/medications (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | create_medication | MedicationActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id}/medications/{medication_id} (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | update_medication | MedicationActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
DELETE /{patient_id}/medications/{medication_id} (apps/api/src/oneepis_api/api/v1/routes/patient_medications.py) | delete_medication | MedicationActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/problems (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | create_active_problem | ProblemActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id}/problems/{problem_id} (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | update_active_problem | ProblemActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
DELETE /{patient_id}/problems/{problem_id} (apps/api/src/oneepis_api/api/v1/routes/patient_problems.py) | delete_active_problem | ProblemActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
POST /{patient_id}/vital-signs (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | create_vital_sign | VitalSignActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
PATCH /{patient_id}/vital-signs/{vital_sign_id} (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | update_vital_sign | VitalSignActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
DELETE /{patient_id}/vital-signs/{vital_sign_id} (apps/api/src/oneepis_api/api/v1/routes/patient_vitals.py) | delete_vital_sign | VitalSignActorDep | record_audit_event | apps/api/tests/test_patient_permissions.py | OK | OK
