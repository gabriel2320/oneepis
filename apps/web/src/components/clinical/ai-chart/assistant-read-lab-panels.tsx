"use client";

import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import type { LabPanel } from "@/lib/types";

import { SourceLine } from "./assistant-read-sections";

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
                {result.reference_range ? (
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    Rango ref.: {result.reference_range}
                  </p>
                ) : null}
                <SourceLine
                  label="lab_result"
                  path={`/api/v1/patients/${panel.patient_id}/lab-panels/${panel.id}/results/${result.id}`}
                  detail={
                    result.status === "entered_in_error"
                      ? "Corregido; fuera de tendencias"
                      : `Estado: ${result.status}`
                  }
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
