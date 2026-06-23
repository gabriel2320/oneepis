"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Clock3, GitCompare, RefreshCw, Search } from "lucide-react";

import {
  CorrelationList,
  DataFootnotes,
  LabPanelList,
  PanelState,
  SearchList,
  SeriesChart,
  SeriesList,
  TimelineList,
} from "@/components/clinical/ai-chart/assistant-read-sections";
import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  correlateAssistant,
  getAssistantChart,
  getAssistantTimeline,
  listLabPanels,
  searchAssistantTimeline,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";

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
  const labPanelsQuery = useQuery({
    queryKey: ["assistant-read", "lab-panels", patientId],
    queryFn: () => listLabPanels(patientId, 3),
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
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="safe">Solo lectura</Badge>
            <Badge variant="outline">Fuentes inspeccionables</Badge>
            <Badge variant="outline">Sin IA externa</Badge>
          </div>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            void timelineQuery.refetch();
            void chartQuery.refetch();
            void correlateQuery.refetch();
            void labPanelsQuery.refetch();
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
          <div className="mt-4">
            <p className="text-sm font-medium">Examenes estructurados recientes</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Lectura de paneles activos/corregidos; las correcciones no alimentan tendencias.
            </p>
            <div className="mt-2">
              <PanelState
                isLoading={labPanelsQuery.isLoading}
                isError={labPanelsQuery.isError}
                empty={labPanelsQuery.data?.length === 0}
                emptyTitle="Sin examenes estructurados"
              >
                <LabPanelList panels={labPanelsQuery.data ?? []} />
              </PanelState>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="correlate">
          <PanelState
            isLoading={correlateQuery.isLoading}
            isError={correlateQuery.isError}
            empty={correlateQuery.data?.correlations.length === 0}
            emptyTitle="Sin correlaciones"
          >
            <CorrelationList correlations={correlateQuery.data?.correlations ?? []} />
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
