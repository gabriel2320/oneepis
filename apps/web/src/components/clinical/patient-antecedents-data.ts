import type { ClinicalEvent, PatientRecordSnapshot } from "@/lib/types";

export type AntecedentSource = "problemas" | "alergias" | "medicacion" | "eventos";

export type AntecedentItem = {
  id: string;
  label: string;
  detail: string;
  context: string;
  category: string;
  source: AntecedentSource;
  href: string;
  occurredAt?: string;
};

export type CuratedAntecedentPayload = {
  category: string;
  source_label: string;
  limit: string;
};

export const antecedentEventTypes = new Set([
  "diagnosis",
  "procedure",
  "clinical_note",
  "care_plan",
]);

export const sourceLabels: Record<AntecedentSource, string> = {
  problemas: "Problemas",
  alergias: "Alergias",
  medicacion: "Medicacion",
  eventos: "Eventos curados",
};

export const sourceDetails: Record<AntecedentSource, string> = {
  problemas: "Diagnosticos/problemas activos registrados.",
  alergias: "Sustancias, reaccion y severidad visibles.",
  medicacion: "Tratamiento activo; no equivale a receta.",
  eventos: "Hechos curados desde timeline clinica.",
};

export const antecedentCategoryLabels: Record<string, string> = {
  problema_activo: "Problema activo",
  alergia: "Alergia",
  medicacion_activa: "Medicacion activa",
  diagnostico_historico: "Diagnostico historico",
  procedimiento: "Procedimiento previo",
  familiar_social: "Familiar/social",
  plan_longitudinal: "Plan longitudinal",
};

export function buildAntecedentItems(
  record: PatientRecordSnapshot,
  patientId: string,
  events: ClinicalEvent[],
): AntecedentItem[] {
  return [
    ...record.active_problems.map((problem) => ({
      id: `problem-${problem.id}`,
      label: problem.title,
      detail: problem.notes ?? `Estado: ${problem.status}`,
      context: problem.code
        ? `${problem.code_system ?? "Codigo"}: ${problem.code}`
        : "Sin codigo clinico estructurado.",
      category: "problema_activo",
      source: "problemas" as const,
      href: `/pacientes/${patientId}/problemas`,
      occurredAt: problem.onset_date ?? undefined,
    })),
    ...record.active_allergies.map((allergy) => ({
      id: `allergy-${allergy.id}`,
      label: allergy.substance,
      detail: allergy.reaction ?? `Severidad: ${allergy.severity}`,
      context: `Severidad: ${allergy.severity}. Estado: ${allergy.status}.`,
      category: "alergia",
      source: "alergias" as const,
      href: `/pacientes/${patientId}/alergias`,
      occurredAt: allergy.recorded_at,
    })),
    ...record.active_medications.map((medication) => ({
      id: `medication-${medication.id}`,
      label: medication.name,
      detail:
        [medication.dose, medication.route, medication.frequency].filter(Boolean).join(" / ") ||
        `Estado: ${medication.status}`,
      context: medication.started_on ? "Con fecha de inicio." : "Sin fecha de inicio.",
      category: "medicacion_activa",
      source: "medicacion" as const,
      href: `/pacientes/${patientId}/medicacion`,
      occurredAt: medication.started_on ?? undefined,
    })),
    ...events.map((event) => eventAntecedentItem(event, patientId)),
  ]
    .filter((item) => item.detail.trim().length > 0)
    .sort((left, right) => compareAntecedentDates(left.occurredAt, right.occurredAt));
}

export function categoryLabel(category: string) {
  return antecedentCategoryLabels[category] ?? category;
}

function eventAntecedentItem(event: ClinicalEvent, patientId: string): AntecedentItem {
  const antecedent = parseCuratedAntecedent(event.payload.antecedent);
  return {
    id: `event-${event.id}`,
    label: event.summary,
    detail: antecedent
      ? `Evento curado como ${categoryLabel(antecedent.category)}`
      : `Evento curado como ${event.event_type}`,
    context: antecedent
      ? `Fuente: ${antecedent.source_label}. Limite: ${antecedent.limit}`
      : `Fuente: ${event.source_type}${event.source_ref ? ` / ${event.source_ref}` : ""}.`,
    category: antecedent?.category ?? event.event_type,
    source: "eventos",
    href: `/pacientes/${patientId}/eventos`,
    occurredAt: event.occurred_at,
  };
}

function parseCuratedAntecedent(value: unknown): CuratedAntecedentPayload | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const item = value as Record<string, unknown>;
  if (
    typeof item.category !== "string" ||
    typeof item.source_label !== "string" ||
    typeof item.limit !== "string"
  ) {
    return null;
  }
  return {
    category: item.category,
    source_label: item.source_label,
    limit: item.limit,
  };
}

function compareAntecedentDates(left?: string, right?: string) {
  if (!left && !right) return 0;
  if (!left) return 1;
  if (!right) return -1;
  return new Date(right).getTime() - new Date(left).getTime();
}
