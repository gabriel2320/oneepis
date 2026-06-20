import { apiFetch } from "@/lib/api/client";
import type {
  AIProviderStatus,
  ClinicalInsightRequest,
  ClinicalInsightResponse,
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
