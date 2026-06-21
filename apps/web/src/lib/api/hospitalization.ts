import { apiFetch } from "@/lib/api/client";
import type {
  HospitalBed,
  HospitalBedCreate,
  HospitalBedUpdate,
  HospitalDailySheet,
  HospitalDailySheetCreate,
  HospitalDailySheetUpdate,
  HospitalIndication,
  HospitalIndicationCreate,
  HospitalIndicationUpdate,
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

export function listHospitalDailySheets(patientId: string) {
  return apiFetch<HospitalDailySheet[]>(
    `/api/v1/hospitalization/patients/${patientId}/daily-sheets?limit=30`,
  );
}

export function createHospitalDailySheet(patientId: string, payload: HospitalDailySheetCreate) {
  return apiFetch<HospitalDailySheet>(
    `/api/v1/hospitalization/patients/${patientId}/daily-sheets`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function updateHospitalDailySheet(
  patientId: string,
  sheetId: string,
  payload: HospitalDailySheetUpdate,
) {
  return apiFetch<HospitalDailySheet>(
    `/api/v1/hospitalization/patients/${patientId}/daily-sheets/${sheetId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export function listHospitalIndications(patientId: string) {
  return apiFetch<HospitalIndication[]>(
    `/api/v1/hospitalization/patients/${patientId}/indications?limit=50`,
  );
}

export function createHospitalIndication(patientId: string, payload: HospitalIndicationCreate) {
  return apiFetch<HospitalIndication>(
    `/api/v1/hospitalization/patients/${patientId}/indications`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function updateHospitalIndication(
  patientId: string,
  indicationId: string,
  payload: HospitalIndicationUpdate,
) {
  return apiFetch<HospitalIndication>(
    `/api/v1/hospitalization/patients/${patientId}/indications/${indicationId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}
