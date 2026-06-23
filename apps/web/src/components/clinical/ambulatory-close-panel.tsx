"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { updateClinicalEncounter } from "@/lib/api/clinical-record";
import type { ClinicalEncounter } from "@/lib/types";

export function AmbulatoryClosePanel({
  patientId,
  encounters,
  disabled,
}: {
  patientId: string;
  encounters: ClinicalEncounter[];
  disabled: boolean;
}) {
  const queryClient = useQueryClient();
  const openEncounters = encounters.filter((encounter) => encounter.status === "in_progress");
  const closeMutation = useMutation({
    mutationFn: (encounterId: string) =>
      updateClinicalEncounter(patientId, encounterId, {
        status: "completed",
        ended_at: new Date().toISOString(),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["clinical-encounters", patientId] }),
      ]);
    },
  });

  return (
    <ClinicalSectionCard
      title="Cierre de consulta"
      description="Cierra el encuentro ambulatorio como estado administrativo; no firma receta ni evolucion."
    >
      {openEncounters.length === 0 ? (
        <EmptyState
          title="Sin encuentros abiertos"
          description="No hay consultas ambulatorias en curso para cerrar."
        />
      ) : (
        <div className="space-y-2">
          {openEncounters.map((encounter) => (
            <article key={encounter.id} className="rounded-md border bg-background p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium">{encounter.reason}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Inicio: {formatDateTime(encounter.started_at)}
                  </p>
                </div>
                <Badge variant="safe">{encounter.status}</Badge>
              </div>
              <Button
                className="mt-3"
                type="button"
                size="sm"
                disabled={disabled || closeMutation.isPending}
                onClick={() => closeMutation.mutate(encounter.id)}
              >
                <CheckCircle2 className="h-4 w-4" />
                {closeMutation.isPending ? "Cerrando..." : "Cerrar encuentro"}
              </Button>
            </article>
          ))}
        </div>
      )}
      {closeMutation.isError ? (
        <p className="mt-3 text-sm text-destructive">
          No se pudo cerrar el encuentro. Revisa API, permisos y auditoria.
        </p>
      ) : null}
      <p className="mt-3 text-xs text-muted-foreground">
        El cierre exige actor y auditoria backend. No genera receta valida, firma clinica ni
        orden ejecutable.
      </p>
    </ClinicalSectionCard>
  );
}
