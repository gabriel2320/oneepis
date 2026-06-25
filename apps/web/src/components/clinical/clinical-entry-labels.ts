import type { ClinicalEntryStatus } from "@/lib/types";

export function formatClinicalEntryStatus(status: ClinicalEntryStatus) {
  if (status === "entered_in_error") {
    return "Anulado";
  }
  if (status === "signed") {
    return "Sin firma legal";
  }
  if (status === "amended") {
    return "Rectificado";
  }
  return "Borrador";
}
