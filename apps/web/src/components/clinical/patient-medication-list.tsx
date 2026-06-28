"use client";

import { Pill } from "lucide-react";

import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import type { Medication, MedicationMissingField } from "@/lib/types";

const MEDICATION_SAFE_READ_COPY = "Lectura clinica. No receta. No dispensacion. No MAR.";

const MEDICATION_MISSING_FIELD_LABELS: Record<MedicationMissingField, string> = {
  dose: "dosis",
  route: "via",
  frequency: "frecuencia",
  source: "fuente",
};

export function MedicationList({ medications }: { medications: Medication[] }) {
  if (medications.length === 0) {
    return <EmptyState title="Sin medicacion activa" description="No hay medicamentos vigentes." />;
  }

  return (
    <div className="space-y-2" role="list" aria-label="Medicacion segura de lectura">
      <p className="rounded-md border border-dashed bg-muted/30 px-2 py-1 text-xs font-medium text-muted-foreground">
        {MEDICATION_SAFE_READ_COPY}
      </p>
      {medications.map((medication) => {
        const missingFields = medication.missing_fields ?? [];
        const missingLabels = missingFields.map((field) => MEDICATION_MISSING_FIELD_LABELS[field]);
        const sourceLabel = medication.source?.source_label ?? "Fuente pendiente";

        return (
          <article key={medication.id} className="rounded-md border p-3" role="listitem">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="flex items-center gap-2 text-sm font-semibold">
                  <Pill className="h-4 w-4 shrink-0 text-primary" />
                  <span className="truncate">{medication.name}</span>
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                {Boolean(medication.dose_check_snapshot?.blocking) ? (
                  <Badge variant="warning">alerta dosis</Badge>
                ) : null}
                <Badge variant="outline">{medication.status}</Badge>
              </div>
            </div>
            <div className="mt-3 grid gap-2 text-xs sm:grid-cols-3">
              <MedicationReadField label="Dosis" value={medication.dose ?? "Pendiente"} />
              <MedicationReadField label="Via" value={medication.route ?? "Pendiente"} />
              <MedicationReadField label="Frecuencia" value={medication.frequency ?? "Pendiente"} />
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Fuente: </span>
              {sourceLabel}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge variant={missingLabels.length > 0 ? "warning" : "safe"}>
                {missingLabels.length > 0
                  ? `Faltantes: ${missingLabels.join(", ")}`
                  : "Sin faltantes declarados"}
              </Badge>
            </div>
          </article>
        );
      })}
    </div>
  );
}

function MedicationReadField({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border bg-muted/20 px-2 py-1.5">
      <p className="text-[11px] font-semibold uppercase text-muted-foreground">{label}</p>
      <p className="truncate text-sm text-foreground">{value}</p>
    </div>
  );
}
