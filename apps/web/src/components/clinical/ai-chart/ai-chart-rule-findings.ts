import type { ClinicalIntentResponse } from "@/lib/types";

export type RuleFindingView = {
  text: string;
  status: "mejora" | "empeora" | "revisar" | "observado";
  source: string;
};

export function groupRuleFindings(items: string[], intent: ClinicalIntentResponse) {
  const groups = [
    { label: "Signos vitales", items: [] as RuleFindingView[] },
    { label: "Curso clinico", items: [] as RuleFindingView[] },
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
      normalized.includes("mejoria clinica") ||
      normalized.includes("empeoramiento clinico")
    ) {
      groups[1].items.push(view);
    } else if (
      normalized.includes("examen") ||
      normalized.includes("creatinina") ||
      normalized.includes("pcr") ||
      normalized.includes("hemoglobina")
    ) {
      groups[2].items.push(view);
    } else if (
      normalized.includes("medicamento") ||
      normalized.includes("medicacion") ||
      normalized.includes("dosis")
    ) {
      groups[3].items.push(view);
    } else if (normalized.includes("revisar") || normalized.includes("sin problema")) {
      groups[4].items.push(view);
    } else {
      groups[5].items.push(view);
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
    normalized.includes("pcr subio") ||
    normalized.includes("empeoramiento clinico")
  ) {
    return "empeora";
  }
  if (
    normalized.includes("saturacion o2 subio") ||
    normalized.includes("temperatura bajo") ||
    normalized.includes("pcr bajo") ||
    normalized.includes("mejoria clinica")
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
  if (normalized.includes("mejoria clinica") || normalized.includes("empeoramiento clinico")) {
    return "clinical_event: evento reciente interpretado por regla local";
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

function hasTokenOverlap(left: string, right: string) {
  const rightTokens = new Set(meaningfulTokens(right));
  return meaningfulTokens(left).some((token) => rightTokens.has(token));
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
