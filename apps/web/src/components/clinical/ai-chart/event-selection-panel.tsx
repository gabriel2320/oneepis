import { BrainCircuit } from "lucide-react";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { DEMO_MODE } from "@/lib/api/client";
import type { ClinicalEvent } from "@/lib/types";

import { formatDate } from "./ai-chart-utils";

type EventSelectionPanelProps = {
  events: ClinicalEvent[];
  selectedIds: string[];
  isGenerating: boolean;
  canUseAi: boolean;
  hasError: boolean;
  onGenerate: () => void;
  onSelectedIdsChange: (ids: string[]) => void;
};

export function EventSelectionPanel({
  events,
  selectedIds,
  isGenerating,
  canUseAi,
  hasError,
  onGenerate,
  onSelectedIdsChange,
}: EventSelectionPanelProps) {
  const blockedReason = eventSelectionBlockedReason({
    selectedCount: selectedIds.length,
    isGenerating,
    canUseAi,
  });
  return (
    <ClinicalSectionCard
      title="Eventos fuente"
      description="Selecciona los hechos que deben entrar al borrador."
      action={
        <Button
          type="button"
          size="sm"
          disabled={Boolean(blockedReason)}
          onClick={onGenerate}
        >
          <BrainCircuit className="h-4 w-4" />
          {isGenerating ? "Generando..." : "Generar SOAP"}
        </Button>
      }
    >
      <EventSelectionList
        events={events}
        selectedIds={selectedIds}
        onSelectedIdsChange={onSelectedIdsChange}
      />
      {blockedReason && !isGenerating ? (
        <p className="mt-3 text-xs text-muted-foreground">{blockedReason}</p>
      ) : null}
      {hasError ? <p className="mt-3 text-sm text-destructive">No se pudieron cargar eventos.</p> : null}
    </ClinicalSectionCard>
  );
}

function eventSelectionBlockedReason({
  selectedCount,
  isGenerating,
  canUseAi,
}: {
  selectedCount: number;
  isGenerating: boolean;
  canUseAi: boolean;
}) {
  if (isGenerating) {
    return "Generando borrador.";
  }
  if (DEMO_MODE) {
    return "Modo demo: no se generan borradores reales.";
  }
  if (!canUseAi) {
    return "Usar IA clinica requiere un perfil autorizado.";
  }
  if (selectedCount === 0) {
    return "Selecciona al menos un evento fuente.";
  }
  return null;
}

function EventSelectionList({
  events,
  selectedIds,
  onSelectedIdsChange,
}: {
  events: ClinicalEvent[];
  selectedIds: string[];
  onSelectedIdsChange: (ids: string[]) => void;
}) {
  if (events.length === 0) {
    return (
      <EmptyState
        title="Sin eventos clinicos"
        description="Registra eventos antes de pedir un borrador SOAP desde AI-Chart."
      />
    );
  }

  return (
    <div className="space-y-2">
      {events.map((event) => {
        const checked = selectedIds.includes(event.id);
        return (
          <label key={event.id} className="flex gap-3 rounded-md border p-3 text-sm">
            <input
              type="checkbox"
              className="mt-1"
              checked={checked}
              onChange={(change) => {
                if (change.target.checked) {
                  onSelectedIdsChange([...selectedIds, event.id]);
                  return;
                }
                onSelectedIdsChange(selectedIds.filter((id) => id !== event.id));
              }}
            />
            <span className="min-w-0">
              <span className="block font-medium">{event.summary}</span>
              <span className="block text-xs text-muted-foreground">
                {event.event_type} - {formatDate(event.occurred_at)}
              </span>
            </span>
          </label>
        );
      })}
    </div>
  );
}
