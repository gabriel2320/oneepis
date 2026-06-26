import type { CareContext, Patient, PatientClinicalStatus } from "@/lib/types";

export function clinicalStatusLabel(status: PatientClinicalStatus) {
  const labels: Record<PatientClinicalStatus, string> = {
    active: "Activa",
    archived: "Archivada",
    closed: "Cerrada",
    draft: "Borrador",
  };
  return labels[status];
}

export function careContextLabel(context: CareContext) {
  const labels: Record<CareContext, string> = {
    ambulatory: "Ambulatoria",
    hospitalized: "Hospitalizada",
    unknown: "Sin contexto",
  };
  return labels[context];
}

export function patientLandingHref(patient: Patient) {
  if (patient.current_care_context === "hospitalized") {
    return `/hospitalizacion/pacientes/${patient.id}/hoja-diaria`;
  }
  if (patient.current_care_context === "ambulatory") {
    return `/consulta/pacientes/${patient.id}/atencion`;
  }
  return `/pacientes/${patient.id}/ficha`;
}
