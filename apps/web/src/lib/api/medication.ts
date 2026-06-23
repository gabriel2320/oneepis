import { apiFetch } from "@/lib/api/client";
import type {
  MedicationCatalogItem,
  MedicationDraftingContext,
  MedicationDraftValidationRequest,
  MedicationDraftValidationResponse,
} from "@/lib/types";

export function listMedicationCatalog(query?: string) {
  const params = new URLSearchParams();
  if (query && query.trim().length >= 2) {
    params.set("q", query.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<MedicationCatalogItem[]>(`/api/v1/medication-catalog${suffix}`);
}

export function getMedicationDraftingContext(patientId: string) {
  return apiFetch<MedicationDraftingContext>(
    `/api/v1/patients/${patientId}/medication-drafting-context`,
  );
}

export function validateMedicationDraft(
  patientId: string,
  payload: MedicationDraftValidationRequest,
) {
  return apiFetch<MedicationDraftValidationResponse>(
    `/api/v1/patients/${patientId}/medications/validate-draft`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
