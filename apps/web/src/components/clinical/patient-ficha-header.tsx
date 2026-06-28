"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PatientRecordSnapshot } from "@/lib/types";

import { formatDateTime } from "./date-format";
import { NoPermissionButton } from "./patient-page-shared";

export function PatientFichaHeader({
  patientId,
  record,
  canEditPatient,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  canEditPatient: boolean;
}) {
  const severeAllergies = record.active_allergies.filter((item) => item.severity === "severe");
  const lastEntry = record.recent_entries[0] ?? null;
  const incompleteMedicationCount = record.active_medications.filter(
    (item) => (item.missing_fields ?? []).length > 0,
  ).length;

  return (
    <div className="rounded-md border bg-card p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0 space-y-1">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Hoja clinica viva</p>
          <p className="text-sm text-muted-foreground">
            Conteos para revisar sin duplicar las listas clinicas del rail.
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-2">
            <FichaHeaderChip label="Problemas" value={`${record.active_problems.length}`} />
            {severeAllergies.length > 0 ? (
              <Badge variant="warning">
                Alergias {record.active_allergies.length} / {severeAllergies.length} criticas
              </Badge>
            ) : (
              <FichaHeaderChip label="Alergias" value={`${record.active_allergies.length}`} />
            )}
            <FichaHeaderChip
              label="Medicamentos"
              value={`${record.active_medications.length} / ${incompleteMedicationCount} incompletos`}
            />
            <FichaHeaderChip label="Evoluciones" value={`${record.recent_entries.length}`} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2" data-print-hidden="true">
          {canEditPatient ? (
            <Button asChild variant="outline" size="sm">
              <Link href={`/pacientes/${patientId}/estado`}>Editar estado</Link>
            </Button>
          ) : (
            <NoPermissionButton label="Estado bloqueado" />
          )}
          <Button asChild variant="outline" size="sm">
            <Link href={`/print/pacientes/${patientId}/ficha`}>Ver papel</Link>
          </Button>
        </div>
      </div>
      <p className="mt-3 border-t pt-3 text-sm text-muted-foreground">
        <span className="font-medium text-foreground">Ultima atencion: </span>
        {lastEntry ? `${lastEntry.title} - ${formatDateTime(lastEntry.occurred_at)}` : "Sin registros"}
      </p>
    </div>
  );
}

function FichaHeaderChip({ label, value }: { label: string; value: string }) {
  return (
    <Badge variant="outline">
      {label} {value}
    </Badge>
  );
}
