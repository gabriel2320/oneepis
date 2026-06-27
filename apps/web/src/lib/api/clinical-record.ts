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
  ClinicalEncounter,
  ClinicalEncounterCreate,
  ClinicalEncounterUpdate,
  ClinicalOrder,
  ClinicalEvent,
  ClinicalEventCreate,
  ClinicalEventUpdate,
  ClinicalTimeline,
  Medication,
  MedicationCreate,
  MedicationUpdate,
  VitalSign,
  VitalSignCreate,
  VitalSignUpdate,
} from "@/lib/types";

export {
  correlateAssistant,
  getAssistantChart,
  getAssistantTimeline,
  listLabPanels,
  searchAssistantTimeline,
} from "@/lib/api/assistant-read";
export {
  confirmClinicalPatch,
  createClinicalIntent,
  decideClinicalIntentAction,
  decideClinicalReviewItem,
  draftSoapFromEvents,
  proposeEventsFromEntry,
  routeClinicalIntent,
  streamClinicalCommandPreview,
} from "@/lib/api/clinical-ai";

export function listClinicalEntries(patientId: string) {
  return apiFetch<ClinicalEntry[]>(`/api/v1/patients/${patientId}/clinical-entries?limit=50`);
}

export const getClinicalEntry = (patientId: string, entryId: string) =>
  apiFetch<ClinicalEntry>(`/api/v1/patients/${patientId}/clinical-entries/${entryId}`);

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

export function listClinicalEvents(patientId: string) {
  return apiFetch<ClinicalEvent[]>(`/api/v1/patients/${patientId}/clinical-events?limit=50`);
}

export function createClinicalEvent(patientId: string, payload: ClinicalEventCreate) {
  return apiFetch<ClinicalEvent>(`/api/v1/patients/${patientId}/clinical-events`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateClinicalEvent(
  patientId: string,
  eventId: string,
  payload: ClinicalEventUpdate,
) {
  return apiFetch<ClinicalEvent>(`/api/v1/patients/${patientId}/clinical-events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getClinicalTimeline(patientId: string) {
  return apiFetch<ClinicalTimeline>(`/api/v1/patients/${patientId}/timeline?limit=50`);
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

export function listClinicalEncounters(patientId: string) {
  return apiFetch<ClinicalEncounter[]>(`/api/v1/patients/${patientId}/encounters?limit=50`);
}

export function createClinicalEncounter(patientId: string, payload: ClinicalEncounterCreate) {
  return apiFetch<ClinicalEncounter>(`/api/v1/patients/${patientId}/encounters`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateClinicalEncounter(
  patientId: string,
  encounterId: string,
  payload: ClinicalEncounterUpdate,
) {
  return apiFetch<ClinicalEncounter>(`/api/v1/patients/${patientId}/encounters/${encounterId}`, {
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

export function listClinicalOrders(patientId: string, limit = 20) {
  return apiFetch<ClinicalOrder[]>(`/api/v1/patients/${patientId}/clinical-orders?limit=${limit}`);
}
