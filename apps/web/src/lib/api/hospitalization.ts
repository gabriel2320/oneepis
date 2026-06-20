import { apiFetch } from "@/lib/api/client";
import type {
  HospitalBed,
  HospitalBedCreate,
  HospitalBedUpdate,
  HospitalizationBoardItem,
} from "@/lib/types";

export function listActiveHospitalizations() {
  return apiFetch<HospitalizationBoardItem[]>("/api/v1/hospitalization/active?limit=50");
}

export function listHospitalBeds() {
  return apiFetch<HospitalBed[]>("/api/v1/hospitalization/beds?limit=100");
}

export function createHospitalBed(payload: HospitalBedCreate) {
  return apiFetch<HospitalBed>("/api/v1/hospitalization/beds", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateHospitalBed(bedId: string, payload: HospitalBedUpdate) {
  return apiFetch<HospitalBed>(`/api/v1/hospitalization/beds/${bedId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
