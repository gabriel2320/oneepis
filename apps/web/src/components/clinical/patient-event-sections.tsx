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
};

const eventCurationPresets: PatientEventCurationPreset[] = [
  {
    label: "Diagnostico historico",
    event_type: "diagnosis",
    summary: "Diagnostico historico por precisar",
    details: "Antecedente leido desde historia clinica. Completar fecha, estado y fuente.",
  },
  {
    label: "Procedimiento previo",
    event_type: "procedure",
    summary: "Procedimiento o cirugia previa por precisar",
    details: "Registrar procedimiento, fecha aproximada, complicaciones y fuente.",
  },
  {
    label: "Antecedente familiar/social",
    event_type: "clinical_note",
    summary: "Antecedente familiar/social por precisar",
    details: "Registrar tipo de antecedente, dato relevante, limite y fuente.",
  },
  {
    label: "Plan o seguimiento",
    event_type: "care_plan",
    summary: "Plan de cuidado longitudinal por precisar",
    details: "Registrar accion humana pendiente, responsable, fecha y fuente.",
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
        Usa eventos existentes para antecedentes hasta definir contrato propio.
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
        </article>
      ))}
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("es-CL", { dateStyle: "short", timeStyle: "short" });
}
