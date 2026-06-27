"use client";

import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { listLabPanels } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type { LabPanel } from "@/lib/types";

type LabBadgeVariant = "safe" | "warning" | "outline";

export function LabResultsPreview({ patientId }: { patientId: string }) {
  const labPanelsQuery = useQuery({
    queryKey: ["lab-panels", patientId, "ficha-preview"],
    queryFn: () => listLabPanels(patientId, 3),
    enabled: !DEMO_MODE,
  });

  return (
    <ClinicalSectionCard
      title="Resultados estructurados"
      description="Lectura reciente de laboratorio con fuente declarada; no permite carga masiva ni ordenes."
    >
      <div className="mb-3 flex flex-wrap gap-2">
        <Badge variant="safe">Solo lectura</Badge>
        <Badge variant="outline">Fuente API</Badge>
        <Badge variant="outline">Fuente declarada</Badge>
        <Badge variant="outline">Sin LIS/RIS/PACS</Badge>
      </div>
      {DEMO_MODE ? (
        <EmptyState
          title="Laboratorio disponible con API real"
          description="Cada resultado incluye origen del panel y ruta API; la ficha demo no simula resultados productivos."
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
      <LabPreviewLimits />
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
  const totalResults = panels.reduce((total, panel) => total + panel.results.length, 0);
  return (
    <div className="space-y-3">
      <div className="grid gap-2 rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground sm:grid-cols-3">
        <div>
          <p className="font-medium text-foreground">{panels.length} paneles</p>
          <p>Ordenados por fecha reciente.</p>
        </div>
        <div>
          <p className="font-medium text-foreground">{totalResults} resultados</p>
          <p>Hasta 4 visibles por panel.</p>
        </div>
        <div>
          <p className="font-medium text-foreground">Fuente estructurada</p>
          <p>Cada resultado expone origen del panel y ruta API.</p>
        </div>
      </div>
      {panels.map((panel) => (
        <div key={panel.id} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium">{panel.panel_name}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(panel.occurred_at)}
              </p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                Origen panel: {panel.source_type}
                {panel.source_ref ? ` / ${panel.source_ref}` : ""}
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
                  <Badge variant={labFlagVariant(result.flag, result.status)}>
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
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{result.source.label}</Badge>
                  <span className="break-all text-[11px] text-muted-foreground">
                    {result.source.request_path}
                  </span>
                </div>
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

function LabPreviewLimits() {
  return (
    <div className="mt-3 rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
      <p className="font-medium text-foreground">Limites visibles y faltantes</p>
      <p className="mt-1">
        Limite visible: 3 paneles recientes y hasta 4 resultados por panel; la vista amplia
        de laboratorio sigue futura.
      </p>
      <p className="mt-1">
        No hay carga masiva, validacion de rangos por edad/sexo ni documento firmado en esta vista.
      </p>
    </div>
  );
}

function labFlagVariant(
  flag: LabPanel["results"][number]["flag"],
  status: LabPanel["status"],
): LabBadgeVariant {
  if (
    status !== "active" ||
    flag === "critical" ||
    flag === "high" ||
    flag === "low" ||
    flag === "abnormal"
  ) {
    return "warning";
  }
  if (flag === "normal") {
    return "safe";
  }
  return "outline";
}

function labPanelSourcePath(panel: LabPanel) {
  return `/api/v1/patients/${panel.patient_id}/lab-panels/${panel.id}`;
}
