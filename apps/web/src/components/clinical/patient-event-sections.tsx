"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClinicalEvent, ClinicalEventType } from "@/lib/types";

import { EmptyState } from "./states";

export type PatientEventCurationPreset = {
  label: string;
  event_type: ClinicalEventType;
  summary: string;
  details: string;
  antecedent: {
    category: "diagnostico_historico" | "procedimiento" | "familiar_social" | "plan_longitudinal";
    source_label: string;
    limit: string;
  };
};

const eventCurationPresets: PatientEventCurationPreset[] = [
  {
    label: "Diagnostico historico",
    event_type: "diagnosis",
    summary: "Diagnostico historico por precisar",
    details: "Antecedente leido desde historia clinica. Completar fecha, estado y fuente.",
    antecedent: {
      category: "diagnostico_historico",
      source_label: "Historia clinica",
      limit: "Fecha, estado y codificacion pendientes de confirmacion humana.",
    },
  },
  {
    label: "Procedimiento previo",
    event_type: "procedure",
    summary: "Procedimiento o cirugia previa por precisar",
    details: "Registrar procedimiento, fecha aproximada, complicaciones y fuente.",
    antecedent: {
      category: "procedimiento",
      source_label: "Relato clinico/documento previo",
      limit: "Fecha exacta y documento fuente pueden estar incompletos.",
    },
  },
  {
    label: "Antecedente familiar/social",
    event_type: "clinical_note",
    summary: "Antecedente familiar/social por precisar",
    details: "Registrar tipo de antecedente, dato relevante, limite y fuente.",
    antecedent: {
      category: "familiar_social",
      source_label: "Entrevista clinica",
      limit: "No equivale a modulo social/familiar estructurado.",
    },
  },
  {
    label: "Plan o seguimiento",
    event_type: "care_plan",
    summary: "Plan de cuidado longitudinal por precisar",
    details: "Registrar accion humana pendiente, responsable, fecha y fuente.",
    antecedent: {
      category: "plan_longitudinal",
      source_label: "Plan humano",
      limit: "Pendiente de seguimiento; no genera orden ni tarea ejecutable.",
    },
  },
];

export function PatientEventCurationPanel({
  disabled,
  onPresetSelect,
}: {
  disabled: boolean;
  onPresetSelect: (preset: PatientEventCurationPreset) => void;
}) {
  return (
    <div className="mb-4 rounded-md border bg-muted/20 p-3">
      <p className="text-xs font-semibold">Curaduria minima para ficha tradicional</p>
      <p className="mt-1 text-xs text-muted-foreground">
        Usa eventos existentes con fuente y limite visible hasta definir contrato propio.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {eventCurationPresets.map((preset) => (
          <Button
            key={preset.label}
            type="button"
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={() => onPresetSelect(preset)}
          >
            {preset.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

export function PatientEventList({ events }: { events: ClinicalEvent[] }) {
  if (events.length === 0) {
    return (
      <EmptyState
        title="Sin eventos registrados"
        description="Registra sintomas, hallazgos, resultados o planes para construir contexto clinico."
      />
    );
  }

  return (
    <div className="space-y-3">
      {events.map((event) => (
        <article key={event.id} className="rounded-md border p-3">
          <div className="flex flex-col gap-1 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="font-medium">{event.summary}</p>
              <p className="text-xs text-muted-foreground">{formatDate(event.occurred_at)}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{event.event_type}</Badge>
              <Badge variant="secondary">Fuente: {event.source_type}</Badge>
            </div>
          </div>
          {typeof event.payload.details === "string" ? (
            <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
              {event.payload.details}
            </p>
          ) : null}
          {isAntecedentPayload(event.payload.antecedent) ? (
            <div className="mt-2 rounded-md bg-muted/30 p-2 text-xs text-muted-foreground">
              <p className="font-medium text-foreground">
                Antecedente curado: {antecedentCategoryLabel(event.payload.antecedent.category)}
              </p>
              <p className="mt-1">Fuente: {event.payload.antecedent.source_label}</p>
              <p className="mt-1">Limite: {event.payload.antecedent.limit}</p>
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("es-CL", { dateStyle: "short", timeStyle: "short" });
}

function isAntecedentPayload(
  value: unknown,
): value is PatientEventCurationPreset["antecedent"] {
  if (!value || typeof value !== "object") {
    return false;
  }
  const item = value as Record<string, unknown>;
  return (
    typeof item.category === "string" &&
    typeof item.source_label === "string" &&
    typeof item.limit === "string"
  );
}

function antecedentCategoryLabel(category: string) {
  const labels: Record<string, string> = {
    diagnostico_historico: "Diagnostico historico",
    procedimiento: "Procedimiento previo",
    familiar_social: "Familiar/social",
    plan_longitudinal: "Plan longitudinal",
  };
  return labels[category] ?? category;
}
