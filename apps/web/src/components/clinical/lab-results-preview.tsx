"use client";

import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { listLabPanels } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type { LabPanel } from "@/lib/types";

export function LabResultsPreview({ patientId }: { patientId: string }) {
  const labPanelsQuery = useQuery({
    queryKey: ["lab-panels", patientId, "ficha-preview"],
    queryFn: () => listLabPanels(patientId, 3),
    enabled: !DEMO_MODE,
  });

  return (
    <ClinicalSectionCard
      title="Resultados estructurados"
      description="Lectura reciente de laboratorio; no permite carga masiva ni ordenes."
    >
      {DEMO_MODE ? (
        <EmptyState
          title="Laboratorio disponible con API real"
          description="La ficha demo no simula resultados productivos."
        />
      ) : null}
      {labPanelsQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {labPanelsQuery.isError ? (
        <ErrorState
          description="No se pudieron cargar resultados estructurados."
          onRetry={() => labPanelsQuery.refetch()}
        />
      ) : null}
      {labPanelsQuery.data ? <LabPanelPreviewList panels={labPanelsQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function LabPanelPreviewList({ panels }: { panels: LabPanel[] }) {
  if (panels.length === 0) {
    return (
      <EmptyState
        title="Sin examenes estructurados"
        description="Assistant Read puede seguir leyendo eventos legacy exam_result."
      />
    );
  }
  return (
    <div className="space-y-3">
      {panels.map((panel) => (
        <div key={panel.id} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium">{panel.panel_name}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(panel.occurred_at)}
              </p>
            </div>
            <Badge variant={panel.status === "active" ? "safe" : "warning"}>{panel.status}</Badge>
          </div>
          {panel.summary ? <p className="mt-2 text-sm text-muted-foreground">{panel.summary}</p> : null}
          <div className="mt-3 space-y-2">
            {panel.results.slice(0, 4).map((result) => (
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
                {result.reference_range ? (
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    Rango ref.: {result.reference_range}
                  </p>
                ) : null}
                <p className="mt-1 text-[11px] text-muted-foreground">
                  {result.status === "entered_in_error"
                    ? "Corregido; fuera de tendencias"
                    : result.numeric_value !== null && result.numeric_value !== undefined
                      ? "Activo y graficable si la serie lo solicita"
                      : "Activo, no graficable sin valor numerico"}
                </p>
                <p className="mt-1 break-all text-[11px] text-muted-foreground">
                  Fuente: {labResultSourcePath(panel, result.id)}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            Fuente panel: {labPanelSourcePath(panel)} - Resultados: {panel.results.length}
          </p>
        </div>
      ))}
    </div>
  );
}

function labPanelSourcePath(panel: LabPanel) {
  return `/api/v1/patients/${panel.patient_id}/lab-panels/${panel.id}`;
}

function labResultSourcePath(panel: LabPanel, resultId: string) {
  return `${labPanelSourcePath(panel)}/results/${resultId}`;
}
