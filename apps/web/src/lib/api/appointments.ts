import { apiFetch } from "@/lib/api/client";
import type {
  ClinicalAppointment,
  ClinicalAppointmentCreate,
  ClinicalAppointmentUpdate,
} from "@/lib/types";

export function listAppointments(dateFrom?: string, dateTo?: string) {
  const params = new URLSearchParams({ limit: "100" });
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return apiFetch<ClinicalAppointment[]>(`/api/v1/appointments?${params.toString()}`);
}

export function listPatientAppointments(patientId: string) {
  return apiFetch<ClinicalAppointment[]>(`/api/v1/patients/${patientId}/appointments?limit=50`);
}

export function createPatientAppointment(patientId: string, payload: ClinicalAppointmentCreate) {
  return apiFetch<ClinicalAppointment>(`/api/v1/patients/${patientId}/appointments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePatientAppointment(
  patientId: string,
  appointmentId: string,
  payload: ClinicalAppointmentUpdate,
) {
  return apiFetch<ClinicalAppointment>(
    `/api/v1/patients/${patientId}/appointments/${appointmentId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}
