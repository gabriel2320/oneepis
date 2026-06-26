import type { ClinicalEncounter } from "@/lib/types";

export const HOSPITALIZATION_ADMISSION_WORKFLOW = "hospitalization_admission" as const;
export const HOSPITALIZATION_DAILY_WORKFLOW = "hospitalization_daily" as const;
export const HOSPITALIZATION_DISCHARGE_WORKFLOW = "hospitalization_discharge" as const;

export function isHospitalizationEncounter(encounter: ClinicalEncounter) {
  return encounter.type === "hospitalization";
}

export function isActiveHospitalizationEncounter(encounter: ClinicalEncounter) {
  return isHospitalizationEncounter(encounter) && encounter.status === "in_progress";
}

export function activeHospitalizationEncounters(encounters: ClinicalEncounter[]) {
  return encounters.filter(isActiveHospitalizationEncounter);
}
