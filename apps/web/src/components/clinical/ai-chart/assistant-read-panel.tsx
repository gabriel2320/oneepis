"use client";

import { useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Clock3, GitCompare, RefreshCw, Search } from "lucide-react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  correlateAssistant,
  getAssistantChart,
  getAssistantTimeline,
  searchAssistantTimeline,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type {
  AssistantChartSeries,
  AssistantCorrelationEvidence,
  AssistantSearchResult,
  AssistantTimelineItem,
} from "@/lib/types";

type AssistantReadPanelProps = {
  patientId: string;
};

export function AssistantReadPanel({ patientId }: AssistantReadPanelProps) {
  const [searchText, setSearchText] = useState("");
  const [submittedSearch, setSubmittedSearch] = useState("");
  const timelineQuery = useQuery({
    queryKey: ["assistant-read", "timeline", patientId],
    queryFn: () => getAssistantTimeline(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const searchQuery = useQuery({
    queryKey: ["assistant-read", "search", patientId, submittedSearch],
    queryFn: () => searchAssistantTimeline(patientId, submittedSearch),
    enabled: Boolean(patientId) && submittedSearch.length >= 2 && !DEMO_MODE,
  });
  const chartQuery = useQuery({
    queryKey: ["assistant-read", "chart", patientId],
    queryFn: () =>
      getAssistantChart(patientId, {
        series: ["heart_rate_bpm", "oxygen_saturation_pct", "exam:creatinina"],
        limit: 80,
      }),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const correlateQuery = useQuery({
    queryKey: ["assistant-read", "correlate", patientId],
    queryFn: () => correlateAssistant(patientId, { limit: 80 }),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const chartSeries = useMemo(() => chartQuery.data?.series ?? [], [chartQuery.data?.series]);
  const primaryChartSeries = useMemo(
    () => chartSeries.find((series) => series.points.length >= 2) ?? chartSeries[0],
    [chartSeries],
  );

  if (DEMO_MODE) {
    return (
      <EmptyState
        title="Assistant Read no disponible en demo"
        description="Usa API real para timeline, busqueda, series y correlacion."
      />
    );
  }

  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium">Assistant Read</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Lectura longitudinal sin escritura clinica.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            void timelineQuery.refetch();
            void chartQuery.refetch();
            void correlateQuery.refetch();
            if (submittedSearch.length >= 2) {
              void searchQuery.refetch();
            }
          }}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refrescar
        </Button>
      </div>
      <Tabs defaultValue="timeline" className="mt-4">
        <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1">
          <TabsTrigger value="timeline">
            <Clock3 className="mr-1.5 h-3.5 w-3.5" />
            Timeline
          </TabsTrigger>
          <TabsTrigger value="search">
            <Search className="mr-1.5 h-3.5 w-3.5" />
            Buscar
          </TabsTrigger>
          <TabsTrigger value="chart">
            <Activity className="mr-1.5 h-3.5 w-3.5" />
            Series
          </TabsTrigger>
          <TabsTrigger value="correlate">
            <GitCompare className="mr-1.5 h-3.5 w-3.5" />
            Correlacion
          </TabsTrigger>
        </TabsList>

        <TabsContent value="timeline">
          <PanelState
            isLoading={timelineQuery.isLoading}
            isError={timelineQuery.isError}
            empty={timelineQuery.data?.items.length === 0}
            emptyTitle="Timeline sin datos"
          >
            <TimelineList items={timelineQuery.data?.items ?? []} />
            <DataFootnotes
              limit={timelineQuery.data?.limit}
              hasMore={timelineQuery.data?.has_more}
              warnings={timelineQuery.data?.warnings ?? []}
              missingData={timelineQuery.data?.missing_data ?? []}
            />
          </PanelState>
        </TabsContent>

        <TabsContent value="search">
          <form
            className="flex flex-col gap-2 sm:flex-row"
            onSubmit={(event) => {
              event.preventDefault();
              setSubmittedSearch(searchText.trim());
            }}
          >
            <Input
              value={searchText}
              placeholder="Buscar antecedente, examen o medicamento"
              onChange={(event) => setSearchText(event.target.value)}
            />
            <Button type="submit" size="sm" disabled={searchText.trim().length < 2}>
              <Search className="h-3.5 w-3.5" />
              Buscar
            </Button>
          </form>
          <div className="mt-3">
            {submittedSearch.length < 2 ? (
              <EmptyState title="Busqueda sin consulta" description="Sin resultados para mostrar." />
            ) : (
              <PanelState
                isLoading={searchQuery.isFetching}
                isError={searchQuery.isError}
                empty={searchQuery.isFetched && searchQuery.data?.results.length === 0}
                emptyTitle="Sin coincidencias"
              >
                <SearchList results={searchQuery.data?.results ?? []} />
                <DataFootnotes
                  limit={searchQuery.data?.limit}
                  hasMore={searchQuery.data?.has_more}
                  warnings={searchQuery.data?.warnings ?? []}
                  missingData={searchQuery.data?.missing_data ?? []}
                />
              </PanelState>
            )}
          </div>
        </TabsContent>

        <TabsContent value="chart">
          <PanelState
            isLoading={chartQuery.isLoading}
            isError={chartQuery.isError}
            empty={chartSeries.length === 0}
            emptyTitle="Sin series"
          >
            {primaryChartSeries ? <SeriesChart series={primaryChartSeries} /> : null}
            <SeriesList series={chartSeries} />
            <DataFootnotes
              limit={chartQuery.data?.limit}
              hasMore={chartQuery.data?.has_more}
              warnings={chartQuery.data?.warnings ?? []}
              missingData={chartQuery.data?.missing_data ?? []}
            />
          </PanelState>
        </TabsContent>

        <TabsContent value="correlate">
          <PanelState
            isLoading={correlateQuery.isLoading}
            isError={correlateQuery.isError}
            empty={correlateQuery.data?.correlations.length === 0}
            emptyTitle="Sin correlaciones"
          >
            <div className="space-y-2">
              {(correlateQuery.data?.correlations ?? []).map((correlation) => (
                <div key={correlation.preset} className="rounded-md border bg-background p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-medium">{correlation.label}</p>
                    <Badge variant="outline">{correlation.preset}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{correlation.summary}</p>
                  <EvidenceList evidence={correlation.evidence} />
                  <DataFootnotes
                    limit={correlation.evidence.length}
                    hasMore={false}
                    warnings={correlation.warnings}
                    missingData={correlation.missing_data}
                  />
                </div>
              ))}
            </div>
            <DataFootnotes
              limit={correlateQuery.data?.limit}
              hasMore={correlateQuery.data?.has_more}
              warnings={correlateQuery.data?.warnings ?? []}
              missingData={correlateQuery.data?.missing_data ?? []}
            />
          </PanelState>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function PanelState({
  isLoading,
  isError,
  empty,
  emptyTitle,
  children,
}: {
  isLoading: boolean;
  isError: boolean;
  empty: boolean;
  emptyTitle: string;
  children: ReactNode;
}) {
  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Cargando...</p>;
  }
  if (isError) {
    return <ErrorState description="No se pudo cargar Assistant Read." />;
  }
  if (empty) {
    return <EmptyState title={emptyTitle} description="No hay datos estructurados para esta vista." />;
  }
  return <>{children}</>;
}

function TimelineList({ items }: { items: AssistantTimelineItem[] }) {
  return (
    <div className="space-y-2">
      {items.slice(0, 8).map((item) => (
        <div key={`${item.item_type}-${item.item_id}`} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium">{item.label}</p>
            <Badge variant="outline">{item.item_type}</Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(item.occurred_at)}</p>
          <p className="mt-1 text-sm">{item.summary}</p>
          <p className="mt-2 text-[11px] text-muted-foreground">Fuente: {item.source_label}</p>
        </div>
      ))}
    </div>
  );
}

function SearchList({ results }: { results: AssistantSearchResult[] }) {
  return (
    <div className="space-y-2">
      {results.slice(0, 8).map((result) => (
        <div key={`${result.item_type}-${result.item_id}`} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium">{result.label}</p>
            <Badge variant="outline">{result.item_type}</Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(result.occurred_at)}</p>
          <p className="mt-1 text-sm">{result.snippet}</p>
          <p className="mt-2 text-[11px] text-muted-foreground">
            Fuente: {result.source_label} - Campos: {result.matched_fields.join(", ") || "fuente"}
          </p>
        </div>
      ))}
    </div>
  );
}

function SeriesChart({ series }: { series: AssistantChartSeries }) {
  const data = series.points.map((point) => ({
    time: new Date(point.occurred_at).toLocaleDateString("es-CL", {
      day: "2-digit",
      month: "2-digit",
    }),
    value: point.value,
  }));
  if (data.length < 2) {
    return null;
  }
  return (
    <div className="mb-3 h-56 rounded-md border bg-background p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">{series.label}</p>
        {series.unit ? <Badge variant="outline">{series.unit}</Badge> : null}
      </div>
      <ResponsiveContainer width="100%" height="82%">
        <LineChart data={data}>
          <XAxis dataKey="time" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} width={36} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function SeriesList({ series }: { series: AssistantChartSeries[] }) {
  return (
    <div className="grid gap-2 md:grid-cols-2">
      {series.slice(0, 6).map((item) => {
        const latest = item.points.at(-1);
        return (
          <div key={item.key} className="rounded-md border bg-background p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium">{item.label}</p>
              <Badge variant="outline">{item.points.length}</Badge>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{item.source_label}</p>
            {latest ? (
              <p className="mt-2 text-sm">
                {latest.value}
                {item.unit ? ` ${item.unit}` : ""} - {formatDateTime(latest.occurred_at)}
              </p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: AssistantCorrelationEvidence[] }) {
  if (evidence.length === 0) {
    return <p className="mt-2 text-xs text-muted-foreground">Sin evidencia suficiente.</p>;
  }
  return (
    <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
      {evidence.slice(0, 4).map((item) => (
        <li key={`${item.source_type}-${item.source_id}-${item.label}`}>
          <span className="font-medium text-foreground">{item.label}</span>: {item.summary} -{" "}
          {formatDateTime(item.occurred_at)} - Fuente: {item.source_path}
        </li>
      ))}
    </ul>
  );
}

function DataFootnotes({
  limit,
  hasMore,
  warnings,
  missingData,
}: {
  limit?: number;
  hasMore?: boolean;
  warnings: string[];
  missingData: string[];
}) {
  const items = [
    typeof limit === "number" ? `Limite aplicado: ${limit}` : null,
    hasMore ? "Hay mas datos que no se muestran en esta vista." : null,
    ...warnings,
    ...missingData,
  ]
    .filter((item): item is string => Boolean(item))
    .slice(0, 4);
  if (items.length === 0) {
    return null;
  }
  return (
    <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}
