import { apiFetch } from "@/lib/api/client";
import type {
  ActiveProblem,
  ActiveProblemCreate,
  ActiveProblemUpdate,
  Allergy,
  AllergyCreate,
  AllergyUpdate,
  AuditEvent,
  AssistantChartRequest,
  AssistantChartResponse,
  AssistantCorrelationRequest,
  AssistantCorrelationResponse,
  AssistantSearchResponse,
  AssistantTimelineResponse,
  ClinicalEntry,
  ClinicalEntryCreate,
  ClinicalEntryUpdate,
  ClinicalEncounter,
  ClinicalEncounterCreate,
  ClinicalEncounterUpdate,
  ClinicalEvent,
  ClinicalEventCreate,
  ClinicalEventUpdate,
  ConfirmClinicalPatchRequest,
  ConfirmClinicalPatchResponse,
  ClinicalIntentRequest,
  ClinicalIntentActionDecisionRequest,
  ClinicalIntentActionDecisionResponse,
  ClinicalIntentRouteRequest,
  ClinicalIntentRouteResponse,
  ClinicalIntentResponse,
  ClinicalReviewItemDecisionRequest,
  ClinicalReviewItemDecisionResponse,
  ClinicalTimeline,
  DraftSoapFromEventsRequest,
  DraftSoapFromEventsResponse,
  EventProposalFromEntryRequest,
  EventProposalsFromEntryResponse,
  AIStreamEvent,
  Medication,
  MedicationCreate,
  MedicationUpdate,
  VitalSign,
  VitalSignCreate,
  VitalSignUpdate,
} from "@/lib/types";
import { API_ACTOR, getStoredAuthToken } from "@/lib/api/client";

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

export function getAssistantTimeline(patientId: string) {
  return apiFetch<AssistantTimelineResponse>(
    `/api/v1/patients/${patientId}/assistant/timeline?limit=20`,
  );
}

export function searchAssistantTimeline(patientId: string, query: string) {
  const params = new URLSearchParams({ q: query, limit: "20" });
  return apiFetch<AssistantSearchResponse>(
    `/api/v1/patients/${patientId}/assistant/search?${params.toString()}`,
  );
}

export function getAssistantChart(patientId: string, payload: AssistantChartRequest = {}) {
  return apiFetch<AssistantChartResponse>(`/api/v1/patients/${patientId}/assistant/chart`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function correlateAssistant(
  patientId: string,
  payload: AssistantCorrelationRequest = {},
) {
  return apiFetch<AssistantCorrelationResponse>(
    `/api/v1/patients/${patientId}/assistant/correlate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function draftSoapFromEvents(patientId: string, payload: DraftSoapFromEventsRequest) {
  return apiFetch<DraftSoapFromEventsResponse>(
    `/api/v1/patients/${patientId}/ai/draft-soap-from-events`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function proposeEventsFromEntry(patientId: string, payload: EventProposalFromEntryRequest) {
  return apiFetch<EventProposalsFromEntryResponse>(
    `/api/v1/patients/${patientId}/ai/event-proposals-from-entry`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function confirmClinicalPatch(patientId: string, payload: ConfirmClinicalPatchRequest) {
  return apiFetch<ConfirmClinicalPatchResponse>(
    `/api/v1/patients/${patientId}/ai/confirm-clinical-patch`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function createClinicalIntent(patientId: string, payload: ClinicalIntentRequest) {
  return apiFetch<ClinicalIntentResponse>(`/api/v1/patients/${patientId}/ai/clinical-intent`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function routeClinicalIntent(patientId: string, payload: ClinicalIntentRouteRequest) {
  return apiFetch<ClinicalIntentRouteResponse>(
    `/api/v1/patients/${patientId}/ai/clinical-intent-route`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function streamClinicalCommandPreview({
  patientId,
  text,
  onEvent,
}: {
  patientId: string;
  text: string;
  onEvent: (event: AIStreamEvent) => void;
}): Promise<ClinicalIntentRouteResponse> {
  const headers = new Headers({ "Content-Type": "application/json" });
  const token = getStoredAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (API_ACTOR) {
    headers.set("X-OneEpis-Actor", API_ACTOR);
  }
  const response = await fetch("/api/ai/clinical-command", {
    method: "POST",
    headers,
    body: JSON.stringify({ patientId, text }),
  });
  if (!response.ok || !response.body) {
    throw new Error("No se pudo abrir el stream clinico.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let routedIntent: ClinicalIntentRouteResponse | null = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) {
        continue;
      }
      const event = JSON.parse(line) as AIStreamEvent;
      onEvent(event);
      if (event.type === "proposal") {
        routedIntent = event.data;
      }
    }
  }
  if (!routedIntent) {
    throw new Error("Stream clinico incompleto.");
  }
  return routedIntent;
}

export function decideClinicalReviewItem(
  patientId: string,
  payload: ClinicalReviewItemDecisionRequest,
) {
  return apiFetch<ClinicalReviewItemDecisionResponse>(
    `/api/v1/patients/${patientId}/ai/review-item-decision`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function decideClinicalIntentAction(
  patientId: string,
  payload: ClinicalIntentActionDecisionRequest,
) {
  return apiFetch<ClinicalIntentActionDecisionResponse>(
    `/api/v1/patients/${patientId}/ai/action-decision`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
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
