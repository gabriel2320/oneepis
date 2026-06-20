import { apiFetch } from "@/lib/api/client";
import type { Patient, PatientCreate, PatientRecordSnapshot, PatientUpdate } from "@/lib/types";

export function listPatients(search?: string) {
  const params = new URLSearchParams({ limit: "50" });
  if (search && search.trim().length >= 2) {
    params.set("search", search.trim());
  }

  return apiFetch<Patient[]>(`/api/v1/patients?${params.toString()}`);
}

export function createPatient(payload: PatientCreate) {
  return apiFetch<Patient>("/api/v1/patients", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePatient(patientId: string, payload: PatientUpdate) {
  return apiFetch<Patient>(`/api/v1/patients/${patientId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getPatient(patientId: string) {
  return apiFetch<Patient>(`/api/v1/patients/${patientId}`);
}

export function getPatientRecord(patientId: string) {
  return apiFetch<PatientRecordSnapshot>(`/api/v1/patients/${patientId}/record`);
}
