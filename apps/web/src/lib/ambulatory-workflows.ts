import type { ClinicalEncounter, ClinicalEntry } from "@/lib/types";

export const AMBULATORY_PRECONSULT_WORKFLOW = "ambulatory_preconsult" as const;
export const AMBULATORY_VISIT_WORKFLOW = "ambulatory_visit" as const;

export function isAmbulatoryEncounter(encounter: ClinicalEncounter) {
  return encounter.type === "ambulatory";
}

export function isAmbulatoryVisitEncounter(encounter: ClinicalEncounter) {
  return isAmbulatoryEncounter(encounter) && encounter.workflow_kind === AMBULATORY_VISIT_WORKFLOW;
}

export function isAmbulatoryPreconsultEncounter(encounter: ClinicalEncounter) {
  return isAmbulatoryEncounter(encounter) && encounter.workflow_kind === AMBULATORY_PRECONSULT_WORKFLOW;
}

export function ambulatoryEncounters(encounters: ClinicalEncounter[]) {
  return encounters.filter(isAmbulatoryEncounter);
}

export function ambulatoryVisitEncounters(encounters: ClinicalEncounter[]) {
  return encounters.filter(isAmbulatoryVisitEncounter);
}

export function ambulatoryEntries(entries: ClinicalEntry[], encounters: ClinicalEncounter[]) {
  const encounterIds = new Set(ambulatoryEncounters(encounters).map((encounter) => encounter.id));
  return entries.filter(
    (entry) =>
      entry.tags.includes("ambulatory") || Boolean(entry.encounter_id && encounterIds.has(entry.encounter_id)),
  );
}
