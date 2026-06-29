"use client";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import type { HistoricalDiagnosis } from "@/lib/types";

export function HistoricalDiagnosisContextCard({
  diagnoses,
  title = "Contexto historico",
  description = "Diagnosticos historicos curados como antecedentes; no son problemas activos ni diagnosticos de egreso.",
}: {
  diagnoses: HistoricalDiagnosis[];
  title?: string;
  description?: string;
}) {
  return (
    <ClinicalSectionCard title={title} description={description}>
      <div className="mb-3 flex flex-wrap gap-2">
        <Badge variant="outline">Antecedente/contexto</Badge>
        <Badge variant="outline">No problema activo</Badge>
        <Badge variant="warning">No diagnostico de egreso</Badge>
      </div>
      {diagnoses.length === 0 ? (
        <EmptyState
          title="Sin diagnosticos historicos curados"
          description="La ficha puede seguir leyendo antecedentes activos, alergias, medicacion y evoluciones."
        />
      ) : (
        <div className="space-y-2">
          {diagnoses.map((diagnosis) => (
            <article key={diagnosis.source_event_id} className="rounded-md border bg-background p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium">{diagnosis.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Fuente: {diagnosis.source_label}
                  </p>
                </div>
                <Badge variant="outline">Historico</Badge>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{diagnosis.limit}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(diagnosis.occurred_at)}
                {diagnosis.code ? ` - ${diagnosis.code_system ?? "Codigo"}: ${diagnosis.code}` : ""}
              </p>
            </article>
          ))}
        </div>
      )}
      <p className="mt-3 text-xs text-muted-foreground">
        Este bloque solo aporta contexto longitudinal y no se copia a diagnosticos de egreso.
      </p>
    </ClinicalSectionCard>
  );
}
