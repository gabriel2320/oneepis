import type {
  AIProviderStatus,
  ClinicalIntentAction,
  ClinicalIntentResponse,
  ClinicalIntentType,
} from "@/lib/types";

export type RuleFindingView = {
  text: string;
  status: "mejora" | "empeora" | "revisar" | "observado";
  source: string;
};

export function clinicalActionKey(action: ClinicalIntentAction) {
  return action.action_id ?? `${action.action_type}-${action.label}`;
}

export function clinicalEventSourceIds(intent: ClinicalIntentResponse) {
  return intent.sources
    .filter((source) => source.source_type === "clinical_event" && source.source_id)
    .map((source) => source.source_id as string);
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
  if (normalized.includes("evolucion") || normalized.includes("soap")) return "draft_soap";
  if (normalized.includes("fuentes")) return "show_sources";
  return null;
}

export function aiStatusLabel(status?: AIProviderStatus, isError = false) {
  if (isError) return "degradada";
  if (!status) return "consultando";
  if (!status.enabled) return "apagada";
  if (!status.available) return "degradada";
  return "activa";
}

export function groupRuleFindings(items: string[], intent: ClinicalIntentResponse) {
  const groups = [
    { label: "Signos vitales", items: [] as RuleFindingView[] },
    { label: "Examenes", items: [] as RuleFindingView[] },
    { label: "Medicacion", items: [] as RuleFindingView[] },
    { label: "Revision", items: [] as RuleFindingView[] },
    { label: "Otros", items: [] as RuleFindingView[] },
  ];
  for (const item of items) {
    const normalized = item.toLocaleLowerCase("es-CL");
    const view = {
      text: item,
      status: ruleFindingStatus(item),
      source: ruleFindingSource(item, intent),
    };
    if (
      normalized.includes("temperatura") ||
      normalized.includes("frecuencia cardiaca") ||
      normalized.includes("presion") ||
      normalized.includes("saturacion")
    ) {
      groups[0].items.push(view);
    } else if (
      normalized.includes("examen") ||
      normalized.includes("creatinina") ||
      normalized.includes("pcr") ||
      normalized.includes("hemoglobina")
    ) {
      groups[1].items.push(view);
    } else if (
      normalized.includes("medicamento") ||
      normalized.includes("medicacion") ||
      normalized.includes("dosis")
    ) {
      groups[2].items.push(view);
    } else if (normalized.includes("revisar") || normalized.includes("sin problema")) {
      groups[3].items.push(view);
    } else {
      groups[4].items.push(view);
    }
  }
  return groups.filter((group) => group.items.length > 0);
}

export function ruleFindingStatus(item: string): RuleFindingView["status"] {
  const normalized = item.toLocaleLowerCase("es-CL");
  if (
    normalized.includes("revisar") ||
    normalized.includes("sin problema") ||
    normalized.includes("sin dosis") ||
    normalized.includes("sin frecuencia") ||
    normalized.includes("medicacion")
  ) {
    return "revisar";
  }
  if (
    normalized.includes("creatinina subio") ||
    normalized.includes("hemoglobina bajo") ||
    normalized.includes("saturacion o2 bajo") ||
    normalized.includes("temperatura subio") ||
    normalized.includes("pcr subio")
  ) {
    return "empeora";
  }
  if (
    normalized.includes("saturacion o2 subio") ||
    normalized.includes("temperatura bajo") ||
    normalized.includes("pcr bajo")
  ) {
    return "mejora";
  }
  return "observado";
}

export function ruleFindingSource(item: string, intent: ClinicalIntentResponse) {
  const matchedSource = intent.sources.find((source) => hasTokenOverlap(item, source.label));
  if (matchedSource) {
    return `${matchedSource.source_type}: ${matchedSource.label}`;
  }

  const matchedNewItem = intent.change_set?.new_items.find((newItem) => hasTokenOverlap(item, newItem));
  if (matchedNewItem) {
    return `clinical_event: ${matchedNewItem}`;
  }

  const normalized = normalizeClinicalText(item);
  if (
    normalized.includes("temperatura") ||
    normalized.includes("frecuencia cardiaca") ||
    normalized.includes("presion") ||
    normalized.includes("saturacion")
  ) {
    return "signos vitales: ultimos dos controles estructurados";
  }
  if (
    normalized.includes("examen") ||
    normalized.includes("creatinina") ||
    normalized.includes("pcr") ||
    normalized.includes("hemoglobina")
  ) {
    return "clinical_event: exam_result estructurado";
  }
  if (
    normalized.includes("medicamento") ||
    normalized.includes("medicacion") ||
    normalized.includes("dosis") ||
    normalized.includes("frecuencia")
  ) {
    return "clinical_event/medication: medicacion estructurada";
  }
  return "contexto clinico estructurado";
}

export function emptyToNull(value?: string | null) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function formatDate(value: string) {
  return new Date(value).toLocaleString("es-CL", { dateStyle: "short", timeStyle: "short" });
}

function hasTokenOverlap(left: string, right: string) {
  const rightTokens = new Set(meaningfulTokens(right));
  return meaningfulTokens(left).some((token) => rightTokens.has(token));
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

function meaningfulTokens(value: string) {
  return normalizeClinicalText(value)
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length >= 4);
}

function normalizeClinicalText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es-CL");
}
