# Traceability Guard - OneEpis

Generado: 2026-06-25T00:38:32.750Z

## Resumen

- Dominios revisados: 11
- Dominios bloqueados permitidos: ClinicalRisk, LabResult
- Fallas: 0

## Matriz

Dominio | Estado | Tabla | patient_id | encounter_id | source_type/source_ref | Auditoria | Bloqueado permitido | Brechas
--- | --- | --- | --- | --- | --- | --- | --- | ---
Patient | READ_MODEL_OK | patients | id propio | no detectado | no requerido en primera pasada | patient.created, patient.updated | no | OK
ClinicalEncounter | READ_MODEL_OK | clinical_encounters | directo | no detectado | no requerido en primera pasada | encounter.cancelled, encounter.created, encounter.updated | no | OK
ClinicalEntry | READ_MODEL_OK | clinical_entries | directo | directo | no requerido en primera pasada | clinical_entry.created, clinical_entry.deleted, clinical_entry.updated | no | OK
ClinicalEvent | READ_MODEL_OK | clinical_events | directo | directo | source_type + source_ref | clinical_event.created, clinical_event.updated | no | OK
VitalSign | READ_MODEL_OK | vital_signs | directo | no detectado | no requerido en primera pasada | vital_sign.created, vital_sign.deleted, vital_sign.updated | no | OK
Allergy | READ_MODEL_OK | allergies | directo | no detectado | no requerido en primera pasada | allergy.created, allergy.entered_in_error, allergy.updated | no | OK
Medication | READ_MODEL_OK | medications | directo | no detectado | no requerido en primera pasada | medication.created, medication.entered_in_error, medication.updated | no | OK
ActiveProblem | READ_MODEL_OK | active_problems | directo | no detectado | no requerido en primera pasada | problem.created, problem.entered_in_error, problem.updated | no | OK
LabResult | DUPLICATED_TRUTH | sin tabla duena dedicada | NO_PATIENT_ID | no detectado | NO_SOURCE_REF | clinical_entry.created, clinical_entry.deleted, clinical_entry.updated, clinical_event.created, clinical_event.updated | si | OK
ClinicalRisk | DUPLICATED_TRUTH | sin tabla duena dedicada | NO_PATIENT_ID | no detectado | NO_SOURCE_REF | no detectada | si | OK
AuditEvent | READ_MODEL_OK | audit_events | indirecto por entity_id/metadata | no detectado | no requerido en primera pasada | no detectada | no | OK
