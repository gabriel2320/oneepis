import type {
  AIProviderStatus,
  ClinicalInsightRequest,
  ClinicalInsightResponse,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export function getAiStatus() {
  return apiFetch<AIProviderStatus>("/api/v1/ai/status");
}

export function createClinicalInsight(payload: ClinicalInsightRequest) {
  return apiFetch<ClinicalInsightResponse>("/api/v1/ai/clinical-insights", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
