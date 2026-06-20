import { apiFetch } from "@/lib/api/client";
import type {
  ActiveProblem,
  ActiveProblemCreate,
  ActiveProblemUpdate,
  Allergy,
  AllergyCreate,
  AllergyUpdate,
  AuditEvent,
  ClinicalEntry,
  ClinicalEntryCreate,
  ClinicalEntryUpdate,
  Medication,
  MedicationCreate,
  MedicationUpdate,
  VitalSign,
  VitalSignCreate,
  VitalSignUpdate,
} from "@/lib/types";

export function listClinicalEntries(patientId: string) {
  return apiFetch<ClinicalEntry[]>(`/api/v1/patients/${patientId}/clinical-entries?limit=50`);
}

export function createClinicalEntry(patientId: string, payload: ClinicalEntryCreate) {
  return apiFetch<ClinicalEntry>(`/api/v1/patients/${patientId}/clinical-entries`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateClinicalEntry(
  patientId: string,
  entryId: string,
  payload: ClinicalEntryUpdate,
) {
  return apiFetch<ClinicalEntry>(`/api/v1/patients/${patientId}/clinical-entries/${entryId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listAllergies(patientId: string) {
  return apiFetch<Allergy[]>(`/api/v1/patients/${patientId}/allergies?limit=50`);
}

export function createAllergy(patientId: string, payload: AllergyCreate) {
  return apiFetch<Allergy>(`/api/v1/patients/${patientId}/allergies`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAllergy(patientId: string, allergyId: string, payload: AllergyUpdate) {
  return apiFetch<Allergy>(`/api/v1/patients/${patientId}/allergies/${allergyId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listMedications(patientId: string) {
  return apiFetch<Medication[]>(`/api/v1/patients/${patientId}/medications?limit=50`);
}

export function createMedication(patientId: string, payload: MedicationCreate) {
  return apiFetch<Medication>(`/api/v1/patients/${patientId}/medications`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateMedication(
  patientId: string,
  medicationId: string,
  payload: MedicationUpdate,
) {
  return apiFetch<Medication>(`/api/v1/patients/${patientId}/medications/${medicationId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listActiveProblems(patientId: string) {
  return apiFetch<ActiveProblem[]>(`/api/v1/patients/${patientId}/problems?limit=50`);
}

export function createActiveProblem(patientId: string, payload: ActiveProblemCreate) {
  return apiFetch<ActiveProblem>(`/api/v1/patients/${patientId}/problems`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateActiveProblem(
  patientId: string,
  problemId: string,
  payload: ActiveProblemUpdate,
) {
  return apiFetch<ActiveProblem>(`/api/v1/patients/${patientId}/problems/${problemId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listVitalSigns(patientId: string) {
  return apiFetch<VitalSign[]>(`/api/v1/patients/${patientId}/vital-signs?limit=50`);
}

export function createVitalSign(patientId: string, payload: VitalSignCreate) {
  return apiFetch<VitalSign>(`/api/v1/patients/${patientId}/vital-signs`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateVitalSign(patientId: string, vitalSignId: string, payload: VitalSignUpdate) {
  return apiFetch<VitalSign>(`/api/v1/patients/${patientId}/vital-signs/${vitalSignId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listAuditEvents(patientId: string) {
  return apiFetch<AuditEvent[]>(`/api/v1/patients/${patientId}/audit-events?limit=80`);
}
