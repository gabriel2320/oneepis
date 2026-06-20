import { apiFetch } from "@/lib/api/client";
import type {
  AIProviderStatus,
  ClinicalInsightRequest,
  ClinicalInsightResponse,
  PatientAiSuggestionRequest,
  PatientAiSuggestionsResponse,
} from "@/lib/types";

export function getAiStatus() {
  return apiFetch<AIProviderStatus>("/api/v1/ai/status");
}

export function createClinicalInsight(payload: ClinicalInsightRequest) {
  return apiFetch<ClinicalInsightResponse>("/api/v1/ai/clinical-insights", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createPatientAiSuggestions(patientId: string, payload: PatientAiSuggestionRequest) {
  return apiFetch<PatientAiSuggestionsResponse>(`/api/v1/patients/${patientId}/ai/suggestions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
