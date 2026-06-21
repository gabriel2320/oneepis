"use client";

import { useQuery } from "@tanstack/react-query";

import { DEMO_MODE } from "@/lib/api/client";
import {
  listActiveHospitalizations,
  listHospitalBeds,
  listHospitalDailySheets,
} from "@/lib/api/hospitalization";
import {
  demoEncounters,
  demoHospitalBeds,
  demoHospitalDailySheets,
  demoRecords,
} from "@/lib/demo-record";
import type { HospitalBedStatus, HospitalizationBoardItem } from "@/lib/types";

export function useHospitalizationBoard() {
  const boardQuery = useQuery({
    queryKey: ["hospitalization-board"],
    queryFn: listActiveHospitalizations,
    enabled: !DEMO_MODE,
  });
  const demoItems = DEMO_MODE ? getDemoHospitalizations() : [];
  return {
    items: DEMO_MODE ? demoItems : (boardQuery.data ?? []),
    isLoading: !DEMO_MODE && boardQuery.isLoading,
    isError: !DEMO_MODE && boardQuery.isError,
    refetch: () => {
      void boardQuery.refetch();
    },
  };
}

export function useHospitalBeds() {
  const bedsQuery = useQuery({
    queryKey: ["hospital-beds"],
    queryFn: listHospitalBeds,
    enabled: !DEMO_MODE,
  });
  return {
    items: DEMO_MODE ? demoHospitalBeds : (bedsQuery.data ?? []),
    isLoading: !DEMO_MODE && bedsQuery.isLoading,
    isError: !DEMO_MODE && bedsQuery.isError,
    refetch: () => {
      void bedsQuery.refetch();
    },
  };
}

export function useHospitalDailySheets(patientId: string) {
  const dailySheetsQuery = useQuery({
    queryKey: ["hospital-daily-sheets", patientId],
    queryFn: () => listHospitalDailySheets(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const demoItems = DEMO_MODE
    ? demoHospitalDailySheets.filter((item) => item.patient_id === patientId)
    : [];
  return {
    items: DEMO_MODE ? demoItems : (dailySheetsQuery.data ?? []),
    isLoading: !DEMO_MODE && dailySheetsQuery.isLoading,
    isError: !DEMO_MODE && dailySheetsQuery.isError,
    refetch: () => {
      void dailySheetsQuery.refetch();
    },
  };
}

export type HospitalizationBoardState = ReturnType<typeof useHospitalizationBoard>;
export type HospitalBedsState = ReturnType<typeof useHospitalBeds>;
export type HospitalDailySheetsState = ReturnType<typeof useHospitalDailySheets>;

export function formatBedLabel(bed: { ward: string; room: string; bed_label: string }) {
  return `${bed.ward} / ${bed.room} / Cama ${bed.bed_label}`;
}

export function formatHospitalizationOption(item: HospitalizationBoardItem) {
  return `${item.patient.first_name} ${item.patient.last_name} - ${item.encounter.reason}`;
}

export function emptyToNull(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export const hospitalBedStatusLabel: Record<HospitalBedStatus, string> = {
  available: "Disponible",
  occupied: "Ocupada",
  cleaning: "Limpieza",
  blocked: "Bloqueada",
};

export const hospitalBedTransitionOptions: {
  value: Exclude<HospitalBedStatus, "occupied">;
  label: string;
}[] = [
  { value: "available", label: "Disponible" },
  { value: "cleaning", label: "Limpieza" },
  { value: "blocked", label: "Bloquear" },
];

function getDemoHospitalizations(): HospitalizationBoardItem[] {
  return demoEncounters
    .filter((encounter) => encounter.type === "hospitalization" && encounter.status === "in_progress")
    .flatMap((encounter) => {
      const record = demoRecords.find((item) => item.patient.id === encounter.patient_id);
      const bed = demoHospitalBeds.find((item) => item.encounter_id === encounter.id) ?? null;
      return record ? [{ patient: record.patient, encounter, bed }] : [];
    });
}
