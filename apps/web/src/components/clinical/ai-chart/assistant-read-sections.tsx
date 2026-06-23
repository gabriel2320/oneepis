"use client";

import type { ReactNode } from "react";
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
import { API_BASE_URL } from "@/lib/api/client";
import type {
  AssistantChartSeries,
  AssistantCorrelationEvidence,
  AssistantCorrelationResult,
  AssistantSearchResult,
  AssistantTimelineItem,
  LabPanel,
} from "@/lib/types";

export function PanelState({
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

export function TimelineList({ items }: { items: AssistantTimelineItem[] }) {
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
          <SourceLine label={item.source_label} path={item.source_path} />
        </div>
      ))}
    </div>
  );
}

export function SearchList({ results }: { results: AssistantSearchResult[] }) {
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
          <SourceLine
            label={result.source_label}
            path={result.source_path}
            detail={`Campos: ${result.matched_fields.join(", ") || "fuente"}`}
          />
        </div>
      ))}
    </div>
  );
}

export function SeriesChart({ series }: { series: AssistantChartSeries }) {
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

export function SeriesList({ series }: { series: AssistantChartSeries[] }) {
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
            <SourceLine label={item.source_label} path={latest?.source_path} />
          </div>
        );
      })}
    </div>
  );
}

export function LabPanelList({ panels }: { panels: LabPanel[] }) {
  if (panels.length === 0) {
    return (
      <EmptyState
        title="Sin examenes estructurados"
        description="Las tendencias pueden seguir leyendo eventos legacy exam_result."
      />
    );
  }
  return (
    <div className="mt-3 space-y-2">
      {panels.slice(0, 3).map((panel) => (
        <div key={panel.id} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium">{panel.panel_name}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(panel.occurred_at)}
              </p>
            </div>
            <Badge variant={panel.status === "active" ? "safe" : "warning"}>{panel.status}</Badge>
          </div>
          {panel.summary ? <p className="mt-2 text-sm">{panel.summary}</p> : null}
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            {panel.results.slice(0, 6).map((result) => (
              <div key={result.id} className="rounded-md bg-muted/30 p-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-medium">{result.name}</p>
                  <Badge variant={result.status === "active" ? "outline" : "warning"}>
                    {result.flag}
                  </Badge>
                </div>
                <p className="mt-1 text-sm">
                  {result.value ?? "Sin valor textual"}
                  {result.unit ? ` ${result.unit}` : ""}
                </p>
                <SourceLine
                  label="lab_result"
                  path={`/api/v1/patients/${panel.patient_id}/lab-panels/${panel.id}/results/${result.id}`}
                  detail={result.status === "entered_in_error" ? "Corregido; fuera de tendencias" : undefined}
                />
              </div>
            ))}
          </div>
          <SourceLine
            label="lab_panel"
            path={`/api/v1/patients/${panel.patient_id}/lab-panels/${panel.id}`}
            detail={`Resultados: ${panel.results.length}`}
          />
        </div>
      ))}
    </div>
  );
}

export function CorrelationList({
  correlations,
}: {
  correlations: AssistantCorrelationResult[];
}) {
  return (
    <div className="space-y-2">
      {correlations.map((correlation) => (
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
          {formatDateTime(item.occurred_at)} - {sourceText(item.source_type, item.source_path)}
        </li>
      ))}
    </ul>
  );
}

function SourceLine({ label, path, detail }: { label: string; path?: string; detail?: string }) {
  return (
    <p className="mt-2 text-[11px] text-muted-foreground" title={path}>
      <span className="break-words">{sourceText(label, path, detail)}</span>
      {path ? (
        <a
          className="ml-2 whitespace-nowrap font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          href={sourceHref(path)}
          target="_blank"
          rel="noreferrer"
          aria-label={`Abrir fuente ${label}`}
        >
          Abrir fuente
        </a>
      ) : null}
    </p>
  );
}

function sourceText(label: string, path?: string, detail?: string) {
  return ["Fuente: " + label, detail, path ?? "ruta no disponible"].filter(Boolean).join(" - ");
}

function sourceHref(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}

export function DataFootnotes({
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
    ...warnings.map((item) => `Advertencia: ${item}`),
    ...missingData.map((item) => `Faltante: ${item}`),
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
