import type { ClinicalIntentAction, ClinicalIntentType } from "@/lib/types";

export function clinicalActionKey(action: ClinicalIntentAction) {
  return action.action_id ?? `${action.action_type}-${action.label}`;
}

export function clinicalActionTarget(patientId: string, action: ClinicalIntentAction) {
  const eventHref = clinicalEventPrefillHref(patientId, action);
  const problemHref = clinicalProblemPrefillHref(patientId, action);
  const medicationHref = clinicalMedicationPrefillHref(patientId, action);
  const allergyHref = clinicalAllergyPrefillHref(patientId, action);
  const vitalHref = clinicalVitalPrefillHref(patientId, action);
  const targets: Partial<Record<ClinicalIntentAction["action_type"], { href: string; label: string }>> = {
    create_event: {
      href: medicationHref ?? allergyHref ?? vitalHref ?? problemHref ?? eventHref,
      label: medicationHref
        ? "Registrar medicacion"
        : allergyHref
          ? "Registrar alergia"
          : vitalHref
            ? "Registrar signos"
            : problemHref
              ? "Registrar problema"
              : "Abrir eventos",
    },
    create_soap_draft: {
      href: `/pacientes/${patientId}/evoluciones/desde-eventos`,
      label: "Crear borrador",
    },
    review_sources: {
      href: `/pacientes/${patientId}/ficha`,
      label: "Revisar ficha",
    },
    add_pending: {
      href: eventHref,
      label: "Registrar pendiente",
    },
  };
  return targets[action.action_type] ?? null;
}

export function clinicalProblemPrefillHref(patientId: string, action: ClinicalIntentAction) {
  const normalizedLabel = normalizedActionText(action);
  if (!normalizedLabel.includes("problema")) {
    return null;
  }
  const params = new URLSearchParams({
    title: action.label,
    notes: action.description ?? "",
  });
  if (action.action_id) {
    params.set("aiActionId", action.action_id);
  }
  return `/pacientes/${patientId}/problemas/nuevo?${params.toString()}`;
}

export function clinicalMedicationPrefillHref(patientId: string, action: ClinicalIntentAction) {
  const normalized = normalizedActionText(action);
  if (!normalized.includes("medicacion") && !normalized.includes("medicamento") && !normalized.includes("farmaco")) {
    return null;
  }
  const params = aiActionParams(action);
  const medicationText = actionClinicalRemainder(action, [
    "registrar",
    "agregar",
    "crear",
    "medicacion",
    "medicamento",
    "farmaco",
    "receta",
  ]);
  if (medicationText) {
    params.set("name", medicationText);
  }
  return `/pacientes/${patientId}/medicacion/nueva?${params.toString()}`;
}

export function clinicalAllergyPrefillHref(patientId: string, action: ClinicalIntentAction) {
  const normalized = normalizedActionText(action);
  if (!normalized.includes("alergia") && !normalized.includes("alergico")) {
    return null;
  }
  const params = aiActionParams(action);
  const substance = actionClinicalRemainder(action, [
    "registrar",
    "agregar",
    "crear",
    "alergia",
    "alergias",
    "alergico",
    "a",
  ]);
  if (substance) {
    params.set("substance", substance);
  }
  return `/pacientes/${patientId}/alergias/nueva?${params.toString()}`;
}

export function clinicalVitalPrefillHref(patientId: string, action: ClinicalIntentAction) {
  const normalized = normalizedActionText(action);
  if (
    !normalized.includes("signos vitales") &&
    !normalized.includes("control de signos") &&
    !normalized.includes("presion") &&
    !normalized.includes("saturacion") &&
    !normalized.includes("temperatura")
  ) {
    return null;
  }
  const params = aiActionParams(action);
  return `/pacientes/${patientId}/signos-vitales/nuevo?${params.toString()}`;
}

export function clinicalEventPrefillHref(patientId: string, action: ClinicalIntentAction) {
  const params = new URLSearchParams({
    eventType: action.action_type === "add_pending" ? "care_plan" : "clinical_note",
    summary: action.label,
    details: action.description ?? "",
  });
  if (action.action_id) {
    params.set("aiActionId", action.action_id);
  }
  return `/pacientes/${patientId}/eventos?${params.toString()}`;
}

export function fallbackActionToIntent(action: ClinicalIntentAction): ClinicalIntentType | null {
  const normalized = (action.action_id ?? action.label).toLocaleLowerCase("es-CL");
  if (normalized.includes("resumir")) return "summarize_patient";
  if (normalized.includes("cambio")) return "daily_changes";
  if (normalized.includes("candidato") || normalized.includes("diagnostico")) {
    return "diagnostic_candidates";
  }
  if (normalized.includes("evolucion") || normalized.includes("soap")) return "draft_soap";
  if (normalized.includes("fuentes")) return "show_sources";
  return null;
}

function normalizedActionText(action: ClinicalIntentAction) {
  return normalizeClinicalText(`${action.action_id ?? ""} ${action.label} ${action.description ?? ""}`);
}

function aiActionParams(action: ClinicalIntentAction) {
  const params = new URLSearchParams();
  if (action.action_id) {
    params.set("aiActionId", action.action_id);
  }
  if (action.description) {
    params.set("sourceText", action.description.slice(0, 600));
  }
  return params;
}

function actionClinicalRemainder(action: ClinicalIntentAction, removableTokens: string[]) {
  const originalText = action.description?.match(/Texto original:\s*(.+)$/)?.[1] ?? "";
  const source = originalText || action.label;
  const removable = new Set(removableTokens.map(normalizeClinicalText));
  const remainder = source
    .split(/\s+/)
    .filter((word) => !removable.has(normalizeClinicalText(word)))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  if (remainder.length < 3 || remainder.length > 120) {
    return "";
  }
  return remainder;
}

function normalizeClinicalText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es-CL");
}
