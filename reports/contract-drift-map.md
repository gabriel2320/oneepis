# Contract Drift Map - OneEpis

Generado: 2026-06-24T22:29:21.413Z

## Resumen

- Contratos revisados: 12
- Contratos con drift: 0

## Matriz

OpenAPI schema | TS type | TS file | Campos OpenAPI | Campos TS | Faltan en TS | Extra en TS
--- | --- | --- | --- | --- | --- | ---
PatientRead | Patient | apps/web/src/lib/type-contracts/patient.ts | birth_date, clinical_identifier, clinical_status, contact_phone, created_at, current_care_context, document_id_hash, email, emergency_contact, first_name, id, last_name, preferred_name, sex_at_birth, updated_at | birth_date, clinical_identifier, clinical_status, contact_phone, created_at, current_care_context, document_id_hash, email, emergency_contact, first_name, id, last_name, preferred_name, sex_at_birth, updated_at | OK | OK
ClinicalEncounterRead | ClinicalEncounter | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, ended_at, id, location_label, notes, patient_id, reason, started_at, status, type, updated_at | created_at, ended_at, id, location_label, notes, patient_id, reason, started_at, status, type, updated_at | OK | OK
ClinicalEntryRead | ClinicalEntry | apps/web/src/lib/type-contracts/clinical-record.ts | assessment, created_at, created_by, encounter_id, extra_data, id, kind, objective, occurred_at, patient_id, plan, status, subjective, tags, title, updated_at | assessment, created_at, created_by, encounter_id, extra_data, id, kind, objective, occurred_at, patient_id, plan, status, subjective, tags, title, updated_at | OK | OK
ClinicalEventRead | ClinicalEvent | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, created_by, encounter_id, event_type, id, occurred_at, patient_id, payload, source_ref, source_type, summary, updated_at | created_at, created_by, encounter_id, event_type, id, occurred_at, patient_id, payload, source_ref, source_type, summary, updated_at | OK | OK
VitalSignRead | VitalSign | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, diastolic_bp, heart_rate_bpm, id, measured_at, notes, oxygen_saturation_pct, patient_id, respiratory_rate_bpm, systolic_bp, temperature_c, updated_at | created_at, diastolic_bp, heart_rate_bpm, id, measured_at, notes, oxygen_saturation_pct, patient_id, respiratory_rate_bpm, systolic_bp, temperature_c, updated_at | OK | OK
AllergyRead | Allergy | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, id, patient_id, reaction, recorded_at, severity, status, substance, updated_at | created_at, id, patient_id, reaction, recorded_at, severity, status, substance, updated_at | OK | OK
MedicationRead | Medication | apps/web/src/lib/type-contracts/clinical-record.ts | created_at, dose, ended_on, frequency, id, name, patient_id, route, started_on, status, updated_at | created_at, dose, ended_on, frequency, id, name, patient_id, route, started_on, status, updated_at | OK | OK
ActiveProblemRead | ActiveProblem | apps/web/src/lib/type-contracts/clinical-record.ts | code, code_system, created_at, id, notes, onset_date, patient_id, resolved_on, status, title, updated_at | code, code_system, created_at, id, notes, onset_date, patient_id, resolved_on, status, title, updated_at | OK | OK
PatientRecordSnapshot | PatientRecordSnapshot | apps/web/src/lib/type-contracts/clinical-record.ts | active_allergies, active_encounter, active_medications, active_problems, latest_vitals, patient, recent_encounters, recent_entries | active_allergies, active_encounter, active_medications, active_problems, latest_vitals, patient, recent_encounters, recent_entries | OK | OK
HospitalBedRead | HospitalBed | apps/web/src/lib/type-contracts/hospitalization.ts | bed_label, created_at, encounter_id, id, notes, room, status, updated_at, ward | bed_label, created_at, encounter_id, id, notes, room, status, updated_at, ward | OK | OK
HospitalDailySheetRead | HospitalDailySheet | apps/web/src/lib/type-contracts/hospitalization.ts | active_plan, clinical_summary, created_at, created_by, encounter_id, id, overnight_events, patient_id, pending_tasks, safety_notes, sheet_date, status, updated_at | active_plan, clinical_summary, created_at, created_by, encounter_id, id, overnight_events, patient_id, pending_tasks, safety_notes, sheet_date, status, updated_at | OK | OK
HospitalIndicationRead | HospitalIndication | apps/web/src/lib/type-contracts/hospitalization.ts | created_at, created_by, encounter_id, id, indicated_at, indication_text, patient_id, rationale, safety_notes, status, title, updated_at | created_at, created_by, encounter_id, id, indicated_at, indication_text, patient_id, rationale, safety_notes, status, title, updated_at | OK | OK
