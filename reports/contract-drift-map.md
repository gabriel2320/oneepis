# Contract Drift Map - OneEpis

Generado: 2026-06-25T02:11:14.564Z

## Resumen

- Contratos revisados: 12
- Contratos con drift: 3
- Contratos con drift no esperado: 0

## Matriz

OpenAPI schema | TS type | TS file | Campos OpenAPI | Campos TS | Faltan en TS | Drift conocido | Drift no esperado | Extra en TS
--- | --- | --- | --- | --- | --- | --- | --- | ---
PatientRead | Patient | apps/web/src/lib/type-contracts/patient.ts | birth_date, clinical_identifier, clinical_status, contact_phone, created_at, current_care_context, document_id_hash, email, emergency_contact, first_name, id, last_name, preferred_name, sex_at_birth, updated_at | birth_date, clinical_identifier, clinical_status, created_at, current_care_context, first_name, id, last_name, preferred_name, sex_at_birth, updated_at | contact_phone, document_id_hash, email, emergency_contact | contact_phone, document_id_hash, email, emergency_contact | OK | OK
ClinicalEncounterRead | ClinicalEncounter | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, ended_at, id, location_label, notes, patient_id, reason, started_at, status, type, updated_at | created_at, ended_at, id, location_label, notes, patient_id, reason, started_at, status, type, updated_at | OK | OK | OK | OK
ClinicalEntryRead | ClinicalEntry | apps/web/src/lib/type-contracts/clinical-record.ts | assessment, created_at, created_by, encounter_id, extra_data, id, kind, objective, occurred_at, patient_id, plan, status, subjective, tags, title, updated_at | assessment, created_at, created_by, encounter_id, id, kind, objective, occurred_at, patient_id, plan, status, subjective, tags, title, updated_at | extra_data | extra_data | OK | OK
ClinicalEventRead | ClinicalEvent | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, created_by, encounter_id, event_type, id, occurred_at, patient_id, payload, source_ref, source_type, summary, updated_at | created_at, created_by, encounter_id, event_type, id, occurred_at, patient_id, payload, source_ref, source_type, summary, updated_at | OK | OK | OK | OK
VitalSignRead | VitalSign | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, diastolic_bp, heart_rate_bpm, id, measured_at, notes, oxygen_saturation_pct, patient_id, respiratory_rate_bpm, systolic_bp, temperature_c, updated_at | created_at, diastolic_bp, heart_rate_bpm, id, measured_at, notes, oxygen_saturation_pct, patient_id, respiratory_rate_bpm, systolic_bp, temperature_c, updated_at | OK | OK | OK | OK
AllergyRead | Allergy | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, id, patient_id, reaction, recorded_at, severity, status, substance, updated_at | created_at, id, patient_id, reaction, recorded_at, severity, status, substance, updated_at | OK | OK | OK | OK
MedicationRead | Medication | apps/web/src/lib/type-contracts/clinical-record.ts | catalog_item_id, created_at, dose, dose_check_snapshot, dose_override_reason, ended_on, frequency, id, name, patient_id, route, started_on, status, updated_at |  | catalog_item_id, created_at, dose, dose_check_snapshot, dose_override_reason, ended_on, frequency, id, name, patient_id, route, started_on, status, updated_at | catalog_item_id, created_at, dose, dose_check_snapshot, dose_override_reason, ended_on, frequency, id, name, patient_id, route, started_on, status, updated_at | OK | OK
ActiveProblemRead | ActiveProblem | apps/web/src/lib/type-contracts/clinical-record.ts | code, code_system, created_at, id, notes, onset_date, patient_id, resolved_on, status, title, updated_at | code, code_system, created_at, id, notes, onset_date, patient_id, resolved_on, status, title, updated_at | OK | OK | OK | OK
PatientRecordSnapshot | PatientRecordSnapshot | apps/web/src/lib/type-contracts/clinical-record.ts | active_allergies, active_medications, active_problems, latest_vitals, patient, recent_entries | active_allergies, active_medications, active_problems, latest_vitals, patient, recent_entries | OK | OK | OK | OK
HospitalBedRead | HospitalBed | apps/web/src/lib/type-contracts/hospitalization.ts | bed_label, created_at, encounter_id, id, notes, room, status, updated_at, ward | bed_label, created_at, encounter_id, id, notes, room, status, updated_at, ward | OK | OK | OK | OK
HospitalDailySheetRead | HospitalDailySheet | apps/web/src/lib/type-contracts/hospitalization.ts | active_plan, clinical_summary, created_at, created_by, encounter_id, id, overnight_events, patient_id, pending_tasks, safety_notes, sheet_date, status, updated_at | active_plan, clinical_summary, created_at, created_by, encounter_id, id, overnight_events, patient_id, pending_tasks, safety_notes, sheet_date, status, updated_at | OK | OK | OK | OK
HospitalIndicationRead | HospitalIndication | apps/web/src/lib/type-contracts/hospitalization.ts | created_at, created_by, encounter_id, id, indicated_at, indication_text, patient_id, rationale, safety_notes, status, title, updated_at | created_at, created_by, encounter_id, id, indicated_at, indication_text, patient_id, rationale, safety_notes, status, title, updated_at | OK | OK | OK | OK
