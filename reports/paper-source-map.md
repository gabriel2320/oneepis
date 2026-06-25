# Paper Source Map - OneEpis

Generado: 2026-06-25T01:42:09.092Z

## Resumen

- Rutas print revisadas: 7
- Rutas app con paperPolicy=carta: 9
- Brechas: 0

## Matriz

Ruta print | Ruta app vinculada | Entidad duena | Read model | Cliente API | Estado documental | Uso clinico | Brechas
--- | --- | --- | --- | --- | --- | --- | ---
/print/pacientes/[patientId]/ficha | /pacientes/[patientId]/ficha | PatientRecordSnapshot | GET /api/v1/patients/{patient_id}/record | apps/web/src/lib/api/patients.ts:getPatientRecord | Documento de desarrollo / no uso clinico real | development-only | OK
/print/pacientes/[patientId]/evolucion/[entryId] | /consulta/pacientes/[patientId]/atencion, /pacientes/[patientId]/evoluciones/desde-eventos, /pacientes/[patientId]/evoluciones/nueva | ClinicalEntry via PatientRecordSnapshot.recent_entries | GET /api/v1/patients/{patient_id}/record | apps/web/src/lib/api/patients.ts:getPatientRecord | Borrador/firmada/enmendada visible; sin firma legal digital | draft-workflow | OK
/print/pacientes/[patientId]/resumen | /consulta/pacientes/[patientId]/resumen | PatientRecordSnapshot | GET /api/v1/patients/{patient_id}/record | apps/web/src/lib/api/patients.ts:getPatientRecord | Documento de desarrollo / no uso clinico real | development-only | OK
/print/pacientes/[patientId]/receta | sin ruta app vinculada | BlockedPrescriptionPlaceholder | GET /api/v1/patients/{patient_id}/record | apps/web/src/lib/api/patients.ts:getPatientRecord | Documento bloqueado: no valido para prescribir | blocked | OK
/print/hospitalizacion/rondas | /hospitalizacion/rondas | HospitalizationBoardItem + latest HospitalDailySheet | GET /api/v1/hospitalization/active + GET /api/v1/hospitalization/patients/{patient_id}/daily-sheets | apps/web/src/lib/api/hospitalization.ts:listActiveHospitalizations,listHospitalDailySheets | Documento operacional de desarrollo / no uso clinico real | development-only | OK
/print/hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId] | /hospitalizacion/pacientes/[patientId]/hoja-diaria, /hospitalizacion/pacientes/[patientId]/hoja-diaria/[sheetId]/editar | HospitalDailySheet + PatientRecordSnapshot | GET /api/v1/patients/{patient_id}/record + GET /api/v1/hospitalization/patients/{patient_id}/daily-sheets | apps/web/src/lib/api/patients.ts:getPatientRecord; apps/web/src/lib/api/hospitalization.ts:listHospitalDailySheets | Borrador/cerrada visible; sin firma legal digital | draft-workflow | OK
/print/hospitalizacion/pacientes/[patientId]/indicacion/[indicationId] | /hospitalizacion/pacientes/[patientId]/indicaciones | HospitalIndication + PatientRecordSnapshot | GET /api/v1/patients/{patient_id}/record + GET /api/v1/hospitalization/patients/{patient_id}/indications | apps/web/src/lib/api/patients.ts:getPatientRecord; apps/web/src/lib/api/hospitalization.ts:listHospitalIndications | Borrador/cerrada visible; no equivale a orden ejecutable ni firma legal | draft-workflow | OK
