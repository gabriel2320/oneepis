"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DEMO_MODE } from "@/lib/api/client";
import { updateHospitalBed } from "@/lib/api/hospitalization";
import { canManageEncounters } from "@/lib/permissions";
import type { HospitalBedCreate } from "@/lib/types";

import {
  formatBedLabel,
  formatHospitalizationOption,
  hospitalBedStatusLabel,
  hospitalBedTransitionOptions,
  type HospitalBedsState,
  type HospitalizationBoardState,
} from "./hospitalization-data";

export function HospitalBedAdminContent({
  beds,
  board,
}: {
  beds: HospitalBedsState;
  board: HospitalizationBoardState;
}) {
  const queryClient = useQueryClient();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageEncounters(user);
  const assignableHospitalizations = board.items.filter((item) => !item.bed);
  const [assignmentByBedId, setAssignmentByBedId] = useState<Record<string, string>>({});
  const mutation = useMutation({
    mutationFn: ({ bedId, payload }: { bedId: string; payload: Partial<HospitalBedCreate> }) =>
      updateHospitalBed(bedId, payload),
    onSuccess: async () => {
      setAssignmentByBedId({});
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["hospital-beds"] }),
        queryClient.invalidateQueries({ queryKey: ["hospitalization-board"] }),
      ]);
    },
  });

  if (beds.isLoading) {
    return <LoadingRows rows={3} />;
  }
  if (beds.isError) {
    return <ErrorState description="No se pudo cargar la administracion de camas." onRetry={beds.refetch} />;
  }
  if (beds.items.length === 0) {
    return (
      <EmptyState
        title="Sin camas registradas"
        description="Crea una cama para iniciar el tablero estructurado."
        action={
          <Button asChild size="sm">
            <Link href="/hospitalizacion/camas/nueva">Nueva cama</Link>
          </Button>
        }
      />
    );
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {beds.items.map((bed) => {
        const assigned = board.items.find((item) => item.encounter.id === bed.encounter_id);
        const selectedEncounterId = assignmentByBedId[bed.id] ?? "";
        const disabled = mutation.isPending || DEMO_MODE || userLoading || !canWrite;
        return (
          <div key={bed.id} className="rounded-md border p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">{formatBedLabel(bed)}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {assigned
                    ? `${assigned.patient.first_name} ${assigned.patient.last_name}`
                    : bed.notes || "Sin paciente asignado"}
                </p>
              </div>
              <Badge variant={bed.status === "blocked" ? "warning" : "safe"}>
                {hospitalBedStatusLabel[bed.status]}
              </Badge>
            </div>
            {bed.encounter_id ? (
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={disabled}
                  onClick={() =>
                    mutation.mutate({
                      bedId: bed.id,
                      payload: { status: "available", encounter_id: null },
                    })
                  }
                >
                  Liberar
                </Button>
              </div>
            ) : (
              <div className="mt-3 space-y-3">
                <label className="block space-y-1 text-sm font-medium">
                  <span>Asignar ingreso</span>
                  <select
                    aria-label={`Asignar ingreso a ${formatBedLabel(bed)}`}
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    disabled={disabled || assignableHospitalizations.length === 0}
                    value={selectedEncounterId}
                    onChange={(event) =>
                      setAssignmentByBedId({
                        ...assignmentByBedId,
                        [bed.id]: event.target.value,
                      })
                    }
                  >
                    <option value="">Seleccionar ingreso</option>
                    {assignableHospitalizations.map((item) => (
                      <option key={item.encounter.id} value={item.encounter.id}>
                        {formatHospitalizationOption(item)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={disabled || !selectedEncounterId}
                    onClick={() =>
                      mutation.mutate({
                        bedId: bed.id,
                        payload: { status: "occupied", encounter_id: selectedEncounterId },
                      })
                    }
                  >
                    Asignar
                  </Button>
                  {hospitalBedTransitionOptions.map((option) => (
                    <Button
                      key={option.value}
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={disabled || bed.status === option.value}
                      onClick={() =>
                        mutation.mutate({
                          bedId: bed.id,
                          payload: { status: option.value, encounter_id: null },
                        })
                      }
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            {mutation.isError ? (
              <p className="mt-2 text-sm text-destructive">No se pudo actualizar la cama.</p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
