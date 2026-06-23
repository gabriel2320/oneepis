"use client";

import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { getClinicalTimeline } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type { ClinicalEntry, ClinicalEvent, ClinicalTimeline } from "@/lib/types";

type TimelineItem = {
  id: string;
  kind: "evolucion" | "evento";
  occurredAt: string;
  title: string;
  summary: string;
  source: string;
};

export function FullTimelinePreview({ patientId }: { patientId: string }) {
  const timelineQuery = useQuery({
    queryKey: ["clinical-timeline", patientId, "ficha-preview"],
    queryFn: () => getClinicalTimeline(patientId),
    enabled: !DEMO_MODE,
  });

  return (
    <ClinicalSectionCard
      title="Linea de tiempo completa"
      description="Lectura combinada de evoluciones y eventos clinicos existentes."
    >
      {DEMO_MODE ? (
        <EmptyState
          title="Timeline completo disponible con API real"
          description="La ficha demo muestra solo evoluciones recientes."
        />
      ) : null}
      {timelineQuery.isLoading ? <LoadingRows rows={3} /> : null}
      {timelineQuery.isError ? (
        <ErrorState
          description="No se pudo cargar la linea de tiempo completa."
          onRetry={() => timelineQuery.refetch()}
        />
      ) : null}
      {timelineQuery.data ? <TimelineItemList timeline={timelineQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function TimelineItemList({ timeline }: { timeline: ClinicalTimeline }) {
  const items = [
    ...timeline.entries.map(entryItem),
    ...timeline.events.map(eventItem),
  ].sort((left, right) => Date.parse(right.occurredAt) - Date.parse(left.occurredAt));

  if (items.length === 0) {
    return (
      <EmptyState
        title="Sin eventos ni evoluciones"
        description="La linea completa se llenara con actos clinicos reales."
      />
    );
  }

  return (
    <div className="space-y-2">
      {items.slice(0, 8).map((item) => (
        <div key={`${item.kind}-${item.id}`} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium">{item.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(item.occurredAt)}
              </p>
            </div>
            <Badge variant="outline">{item.kind}</Badge>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{item.summary}</p>
          <p className="mt-2 text-[11px] text-muted-foreground">Fuente: {item.source}</p>
        </div>
      ))}
    </div>
  );
}

function entryItem(entry: ClinicalEntry): TimelineItem {
  return {
    id: entry.id,
    kind: "evolucion",
    occurredAt: entry.occurred_at,
    title: entry.title,
    summary: entry.assessment || entry.plan || entry.subjective || "Evolucion sin resumen.",
    source: "clinical_entries",
  };
}

function eventItem(event: ClinicalEvent): TimelineItem {
  return {
    id: event.id,
    kind: "evento",
    occurredAt: event.occurred_at,
    title: event.event_type,
    summary: event.summary,
    source: "clinical_events",
  };
}
