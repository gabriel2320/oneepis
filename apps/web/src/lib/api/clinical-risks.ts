import { apiFetch } from "@/lib/api/client";
import type { ClinicalRisk, ClinicalRiskCreate, ClinicalRiskUpdate, RecordStatus } from "@/lib/types";

export function listClinicalRisks(patientId: string, status?: RecordStatus, limit = 20) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) {
    params.set("status", status);
  }
  return apiFetch<ClinicalRisk[]>(
    `/api/v1/patients/${patientId}/clinical-risks?${params.toString()}`,
  );
}

export function createClinicalRisk(patientId: string, payload: ClinicalRiskCreate) {
  return apiFetch<ClinicalRisk>(`/api/v1/patients/${patientId}/clinical-risks`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateClinicalRisk(
  patientId: string,
  riskId: string,
  payload: ClinicalRiskUpdate,
) {
  return apiFetch<ClinicalRisk>(`/api/v1/patients/${patientId}/clinical-risks/${riskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
