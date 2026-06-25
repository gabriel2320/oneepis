# Snapshot Usage Map - OneEpis

Generado: 2026-06-25T02:08:12.695Z

## Resumen

- Read models frontend: 15
- Snapshots/proyecciones: 5
- Read models sin consumidor visible: 5

## Matriz

Funcion | Rol | Endpoint | Tipo retorno | Cliente | Consumidores
--- | --- | --- | --- | --- | ---
getPatient | entity-list | /api/v1/patients/{patientId} | Patient | apps/web/src/lib/api/patients.ts | no detectado
getPatientRecord | patient-record-snapshot | /api/v1/patients/{patientId}/record | PatientRecordSnapshot | apps/web/src/lib/api/patients.ts | apps/web/src/components/clinical/patient-page-shared.tsx, apps/web/src/components/print/clinical-print.tsx, apps/web/src/components/print/hospital-admission-print.tsx, apps/web/src/components/print/hospital-discharge-summary-print.tsx, apps/web/src/components/print/hospital-indication-print.tsx
listClinicalEntries | entity-list | /api/v1/patients/{patientId}/clinical-entries?limit=50 | ClinicalEntry[] | apps/web/src/lib/api/clinical-record.ts | no detectado
listClinicalEvents | entity-list | /api/v1/patients/{patientId}/clinical-events?limit=50 | ClinicalEvent[] | apps/web/src/lib/api/clinical-record.ts | apps/web/src/components/clinical/patient-ai-chart-pages.tsx, apps/web/src/components/clinical/patient-event-pages.tsx
getClinicalTimeline | timeline-projection | /api/v1/patients/{patientId}/timeline?limit=50 | ClinicalTimeline | apps/web/src/lib/api/clinical-record.ts | apps/web/src/components/clinical/patient-antecedents-preview.tsx
listAllergies | entity-list | /api/v1/patients/{patientId}/allergies?limit=50 | Allergy[] | apps/web/src/lib/api/clinical-record.ts | no detectado
listMedications | entity-list | /api/v1/patients/{patientId}/medications?limit=50 | Medication[] | apps/web/src/lib/api/clinical-record.ts | no detectado
listActiveProblems | entity-list | /api/v1/patients/{patientId}/problems?limit=50 | ActiveProblem[] | apps/web/src/lib/api/clinical-record.ts | no detectado
listClinicalEncounters | entity-list | /api/v1/patients/{patientId}/encounters?limit=50 | ClinicalEncounter[] | apps/web/src/lib/api/clinical-record.ts | apps/web/src/components/clinical/ambulatory-summary-pages.tsx, apps/web/src/components/clinical/ambulatory-visit-pages.tsx, apps/web/src/components/clinical/hospital-admission-pages.tsx, apps/web/src/components/clinical/hospital-discharge-summary-pages.tsx, apps/web/src/components/clinical/patient-event-pages.tsx, apps/web/src/components/clinical/patient-record-workspaces.tsx (+1 mas)
listVitalSigns | entity-list | /api/v1/patients/{patientId}/vital-signs?limit=50 | VitalSign[] | apps/web/src/lib/api/clinical-record.ts | apps/web/src/components/clinical/patient-record-workspaces.tsx
listAuditEvents | entity-list | /api/v1/patients/{patientId}/audit-events?limit=80 | AuditEvent[] | apps/web/src/lib/api/clinical-record.ts | apps/web/src/components/clinical/patient-record-workspaces.tsx
listActiveHospitalizations | hospitalization-board-projection | /api/v1/hospitalization/active?limit=50 | HospitalizationBoardItem[] | apps/web/src/lib/api/hospitalization.ts | apps/web/src/components/clinical/hospitalization-data.ts, apps/web/src/components/print/hospital-round-print.tsx
listHospitalBeds | entity-list | /api/v1/hospitalization/beds?limit=100 | HospitalBed[] | apps/web/src/lib/api/hospitalization.ts | apps/web/src/components/clinical/hospitalization-data.ts
listHospitalDailySheets | hospital-document-list | /api/v1/hospitalization/patients/{patientId}/daily-sheets?limit=30 | HospitalDailySheet[] | apps/web/src/lib/api/hospitalization.ts | apps/web/src/components/clinical/hospitalization-data.ts, apps/web/src/components/print/clinical-print.tsx, apps/web/src/components/print/hospital-round-print.tsx
listHospitalIndications | hospital-document-list | /api/v1/hospitalization/patients/{patientId}/indications?limit=50 | HospitalIndication[] | apps/web/src/lib/api/hospitalization.ts | apps/web/src/components/clinical/hospitalization-data.ts, apps/web/src/components/print/hospital-indication-print.tsx
