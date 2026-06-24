import { API_ACTOR, apiFetch, getStoredAuthToken } from "@/lib/api/client";
import type {
  AIStreamEvent,
  ClinicalIntentActionDecisionRequest,
  ClinicalIntentActionDecisionResponse,
  ClinicalIntentRequest,
  ClinicalIntentResponse,
  ClinicalIntentRouteRequest,
  ClinicalIntentRouteResponse,
  ClinicalReviewItemDecisionRequest,
  ClinicalReviewItemDecisionResponse,
  ConfirmClinicalPatchRequest,
  ConfirmClinicalPatchResponse,
  DraftSoapFromEventsRequest,
  DraftSoapFromEventsResponse,
  EventProposalFromEntryRequest,
  EventProposalsFromEntryResponse,
} from "@/lib/types";

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
