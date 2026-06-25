# Encounter Axis Map - OneEpis

Generado: 2026-06-25T02:09:58.846Z

## Resumen

- Dominios revisados: 10
- Required encounter OK: 2
- Optional encounter OK: 2
- Longitudinales no forzados: 4
- Seguimientos requeridos: 0

## Politica

Este reporte no cambia modelos. C7 solo declara donde `encounter_id` ya es eje clinico, donde es opcional y donde no debe forzarse sin decision clinica.

## Matriz

Dominio | Expectativa | Modelo encounter_id | Validacion | Estado | Recomendacion
--- | --- | --- | --- | --- | ---
ClinicalEncounter | EPISODE_OWNER | not_applicable | no aplica: entidad dueña | OK | Es la entidad dueña del episodio; no debe tener encounter_id propio.
ClinicalEntry | OPTIONAL_ENCOUNTER | optional | validate_encounter_for_patient | OK | SOAP/evolucion puede ser longitudinal, pero debe vincularse cuando existe episodio activo.
ClinicalEvent | OPTIONAL_ENCOUNTER | optional | validate_encounter_for_patient | OK | Hecho longitudinal puede nacer fuera de un episodio, pero debe heredar encuentro cuando viene de acto clinico.
HospitalBed | OPTIONAL_ASSIGNMENT | optional | no detectada | OK | La cama puede existir sin paciente; encounter_id aparece solo cuando se asigna a ingreso.
HospitalDailySheet | REQUIRED_ENCOUNTER | required | _require_active_hospitalization | OK | Hoja diaria hospitalaria pertenece a un ingreso hospitalario activo.
HospitalIndication | REQUIRED_ENCOUNTER | required | _require_active_hospitalization | OK | Indicacion hospitalaria minima pertenece a un ingreso hospitalario activo.
VitalSign | PATIENT_LONGITUDINAL | not_applicable | no detectada | OK | Signo vital vive por paciente; si explica episodio, se proyecta como ClinicalEvent con source_type vital_sign.
Allergy | PATIENT_LONGITUDINAL | not_applicable | no detectada | OK | Alergia es longitudinal del paciente; no forzar episodio sin decision clinica.
Medication | PATIENT_LONGITUDINAL | not_applicable | no detectada | OK | Medicacion activa no es receta ni orden; no forzar episodio hasta definir prescripcion legal.
ActiveProblem | PATIENT_LONGITUDINAL | not_applicable | no detectada | OK | Problema activo puede cruzar episodios; el origen debe trazarse con eventos/evoluciones si aplica.
