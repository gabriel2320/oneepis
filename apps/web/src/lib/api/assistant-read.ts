import { apiFetch } from "@/lib/api/client";
import type {
  AssistantChartRequest,
  AssistantChartResponse,
  AssistantCorrelationRequest,
  AssistantCorrelationResponse,
  AssistantSearchResponse,
  AssistantTimelineResponse,
  LabPanel,
} from "@/lib/types";

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

export function listLabPanels(patientId: string, limit = 3) {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiFetch<LabPanel[]>(`/api/v1/patients/${patientId}/lab-panels?${params.toString()}`);
}
