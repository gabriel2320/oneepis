import { apiFetch } from "@/lib/api/client";
import type { HospitalizationBoardItem } from "@/lib/types";

export function listActiveHospitalizations() {
  return apiFetch<HospitalizationBoardItem[]>("/api/v1/hospitalization/active?limit=50");
}
