import type { AIProviderStatus, ClinicalIntentResponse } from "@/lib/types";

export {
  clinicalActionKey,
  clinicalActionTarget,
  clinicalAllergyPrefillHref,
  clinicalEventPrefillHref,
  clinicalMedicationPrefillHref,
  clinicalProblemPrefillHref,
  clinicalVitalPrefillHref,
  fallbackActionToIntent,
} from "./ai-chart-action-targets";
export {
  groupRuleFindings,
  ruleFindingSource,
  ruleFindingStatus,
  type RuleFindingView,
} from "./ai-chart-rule-findings";

export function clinicalEventSourceIds(intent: ClinicalIntentResponse) {
  return intent.sources
    .filter((source) => source.source_type === "clinical_event" && source.source_id)
    .map((source) => source.source_id as string);
}

export function aiStatusLabel(status?: AIProviderStatus, isError = false) {
  if (isError) return "degradada";
  if (!status) return "consultando";
  if (!status.enabled) return "apagada";
  if (!status.available) return "degradada";
  return "activa";
}

export function emptyToNull(value?: string | null) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function formatDate(value: string) {
  return new Date(value).toLocaleString("es-CL", { dateStyle: "short", timeStyle: "short" });
}
