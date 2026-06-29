"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAssistantTimeline } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type {
  AssistantTimelineItem,
  AssistantTimelineItemType,
  AssistantTimelineResponse,
} from "@/lib/types";

type TimelineFilter = AssistantTimelineItemType | "all";

const TIMELINE_FILTERS: Array<{ value: TimelineFilter; label: string }> = [
  { value: "all", label: "Todo" },
  { value: "clinical_entry", label: "Evoluciones" },
  { value: "clinical_event", label: "Eventos" },
  { value: "encounter", label: "Atenciones" },
  { value: "vital_sign", label: "Signos" },
  { value: "medication", label: "Medicacion" },
  { value: "problem", label: "Antecedentes" },
  { value: "allergy", label: "Alergias" },
  { value: "lab_result", label: "Laboratorio" },
];

const TYPE_LABELS: Record<AssistantTimelineItemType, string> = {
  encounter: "Atencion/ingreso",
  clinical_entry: "Evolucion",
  clinical_event: "Evento",
  vital_sign: "Signos vitales",
  medication: "Medicacion",
  problem: "Antecedente",
  allergy: "Alergia",
  lab_result: "Laboratorio",
};

export function FullTimelinePreview({ patientId }: { patientId: string }) {
  const timelineQuery = useQuery({
    queryKey: ["assistant-timeline", patientId, "ficha-preview"],
    queryFn: () => getAssistantTimeline(patientId),
    enabled: !DEMO_MODE,
  });

  return (
    <ClinicalSectionCard
      title="Linea de tiempo avanzada"
      description="Lectura longitudinal de fuentes clinicas existentes, sin escritura automatica."
    >
      <div className="mb-3 flex flex-wrap gap-2">
        <Badge variant="safe">Solo lectura</Badge>
        <Badge variant="outline">Fuentes visibles</Badge>
        <Badge variant="outline">Sin IA protagonista</Badge>
        <Badge variant="outline">No escribe ficha</Badge>
      </div>
      {DEMO_MODE ? (
        <EmptyState
          title="Timeline avanzado disponible con API real"
          description="La ficha demo no simula datos longitudinales avanzados."
        />
      ) : null}
      {timelineQuery.isLoading ? <LoadingRows rows={3} /> : null}
      {timelineQuery.isError ? (
        <ErrorState
          description="No se pudo cargar la linea de tiempo avanzada."
          onRetry={() => timelineQuery.refetch()}
        />
      ) : null}
      {timelineQuery.data ? <TimelineWorkspace timeline={timelineQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function TimelineWorkspace({ timeline }: { timeline: AssistantTimelineResponse }) {
  const [activeFilter, setActiveFilter] = useState<TimelineFilter>("all");
  const counts = useMemo(() => countByType(timeline.items), [timeline.items]);
  const filteredItems = useMemo(() => {
    if (activeFilter === "all") {
      return timeline.items;
    }
    return timeline.items.filter((item) => item.item_type === activeFilter);
  }, [activeFilter, timeline.items]);

  if (timeline.items.length === 0) {
    return (
      <>
        <EmptyState
          title="Sin datos longitudinales"
          description="La linea avanzada se llenara con actos clinicos reales."
        />
        <TimelineFootnotes timeline={timeline} />
      </>
    );
  }

  return (
    <div className="space-y-3">
      <TimelineScopeSummary timeline={timeline} filteredCount={filteredItems.length} />
      <TimelineFilters
        activeFilter={activeFilter}
        counts={counts}
        onChange={setActiveFilter}
        totalCount={timeline.items.length}
      />
      <TimelineItemList activeFilter={activeFilter} items={filteredItems} />
      <TimelineFootnotes timeline={timeline} />
    </div>
  );
}

function TimelineScopeSummary({
  timeline,
  filteredCount,
}: {
  timeline: AssistantTimelineResponse;
  filteredCount: number;
}) {
  const sourceCount = new Set(timeline.items.map((item) => item.source_label)).size;
  return (
    <div className="grid gap-2 rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground sm:grid-cols-3">
      <div>
        <p className="font-medium text-foreground">{timeline.items.length} registros</p>
        <p>Lectura longitudinal combinada.</p>
      </div>
      <div>
        <p className="font-medium text-foreground">{sourceCount} fuentes</p>
        <p>API existente, sin tabla nueva.</p>
      </div>
      <div>
        <p className="font-medium text-foreground">{filteredCount} visibles</p>
        <p>Segun filtro activo.</p>
      </div>
    </div>
  );
}

function TimelineFilters({
  activeFilter,
  counts,
  onChange,
  totalCount,
}: {
  activeFilter: TimelineFilter;
  counts: Partial<Record<AssistantTimelineItemType, number>>;
  onChange: (filter: TimelineFilter) => void;
  totalCount: number;
}) {
  return (
    <div className="flex flex-wrap gap-2" aria-label="Filtros de linea de tiempo">
      {TIMELINE_FILTERS.map((filter) => {
        const count = filter.value === "all" ? totalCount : (counts[filter.value] ?? 0);
        const isActive = activeFilter === filter.value;
        return (
          <Button
            key={filter.value}
            type="button"
            variant={isActive ? "default" : "outline"}
            size="sm"
            className="gap-2"
            onClick={() => onChange(filter.value)}
            aria-pressed={isActive}
          >
            {filter.label}
            <span className="text-[11px] opacity-80">{count}</span>
          </Button>
        );
      })}
    </div>
  );
}

function TimelineItemList({
  activeFilter,
  items,
}: {
  activeFilter: TimelineFilter;
  items: AssistantTimelineItem[];
}) {
  if (items.length === 0) {
    return (
      <EmptyState
        title="Sin datos para este filtro"
        description={`No hay registros recientes en ${filterLabel(activeFilter).toLowerCase()}.`}
      />
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <article
          key={`${item.item_type}-${item.item_id}-${item.occurred_at}`}
          className="rounded-md border bg-background p-3"
        >
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium">{item.label}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(item.occurred_at)}
              </p>
            </div>
            <Badge variant="outline">{TYPE_LABELS[item.item_type]}</Badge>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{item.summary}</p>
          <div className="mt-2 space-y-1 text-[11px] text-muted-foreground">
            <p>Fuente: {item.source_label}</p>
            <p>Tipo clinico: {timelineTypeLabel(item)}</p>
            <details>
              <summary className="cursor-pointer font-medium text-foreground">
                Detalle tecnico
              </summary>
              <p className="mt-1 break-all">Ruta: {item.source_path}</p>
            </details>
          </div>
        </article>
      ))}
    </div>
  );
}

function TimelineFootnotes({ timeline }: { timeline: AssistantTimelineResponse }) {
  const notes = [
    `Limite aplicado: ${timeline.limit}`,
    timeline.has_more ? "Hay mas datos longitudinales fuera de esta vista." : null,
    ...timeline.warnings.map((warning) => `Advertencia: ${warning}`),
    ...timeline.missing_data.map((item) => `Faltante: ${item}`),
  ].filter((item): item is string => Boolean(item));

  if (notes.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
      <p className="font-medium text-foreground">Limites y faltantes</p>
      <ul className="mt-2 space-y-1">
        {notes.slice(0, 6).map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </div>
  );
}

function countByType(items: AssistantTimelineItem[]) {
  return items.reduce<Partial<Record<AssistantTimelineItemType, number>>>((counts, item) => {
    counts[item.item_type] = (counts[item.item_type] ?? 0) + 1;
    return counts;
  }, {});
}

function filterLabel(filter: TimelineFilter) {
  if (filter === "all") {
    return "todo";
  }
  return TYPE_LABELS[filter];
}

function timelineTypeLabel(item: AssistantTimelineItem) {
  if (item.item_type === "clinical_event" && item.source_label !== "clinical_events") {
    return "Diagnostico historico";
  }
  return TYPE_LABELS[item.item_type];
}
