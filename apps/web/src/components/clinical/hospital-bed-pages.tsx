"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { DomainModulePage } from "@/components/clinical/clinical-domain-module";
import { HospitalBedAdminContent } from "@/components/clinical/hospital-bed-admin";
import { BedBoard } from "@/components/clinical/hospitalization-widgets";
import { ErrorState, LoadingRows } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { DEMO_MODE } from "@/lib/api/client";
import { createHospitalBed } from "@/lib/api/hospitalization";
import { canManageEncounters } from "@/lib/permissions";
import type { HospitalBedCreate, HospitalBedStatus } from "@/lib/types";

import {
  emptyToNull,
  formatHospitalizationOption,
  useHospitalBeds,
  useHospitalizationBoard,
  type HospitalizationBoardState,
} from "./hospitalization-data";

export function HospitalBedsPage() {
  const board = useHospitalizationBoard();
  const beds = useHospitalBeds();

  return (
    <DomainModulePage
      domain="hospital"
      title="Camas"
      description="Tablero hospitalario desde ingresos activos."
      actions={[{ href: "/hospitalizacion/camas/nueva", label: "Registrar cama" }]}
    >
      <div className="space-y-4">
        <ClinicalSectionCard title="Pacientes hospitalizados">
          <HospitalizationBoardContent board={board} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Administracion de camas">
          <HospitalBedAdminContent beds={beds} board={board} />
        </ClinicalSectionCard>
      </div>
    </DomainModulePage>
  );
}

export function NewHospitalBedPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const board = useHospitalizationBoard();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageEncounters(user);
  const [formState, setFormState] = useState({
    ward: "",
    room: "",
    bed_label: "",
    status: "available" as Exclude<HospitalBedStatus, "occupied">,
    encounter_id: "",
    notes: "",
  });
  const mutation = useMutation({
    mutationFn: (payload: HospitalBedCreate) => createHospitalBed(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["hospital-beds"] }),
        queryClient.invalidateQueries({ queryKey: ["hospitalization-board"] }),
      ]);
      router.push("/hospitalizacion/camas");
    },
  });
  const assignableHospitalizations = board.items.filter((item) => !item.bed);
  const selectedEncounterId = emptyToNull(formState.encounter_id);

  return (
    <DomainModulePage domain="hospital" title="Registrar cama" description="Cama hospitalaria estructurada y auditada.">
      <div className="max-w-xl space-y-5">
        <Button asChild variant="outline" size="sm">
          <Link href="/hospitalizacion/camas">Volver a camas</Link>
        </Button>
        {DEMO_MODE ? <ErrorState description="El modo demo no permite crear camas reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu perfil no tiene permiso para administrar camas." />
        ) : null}
        <ClinicalSectionCard title="Cama">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                ward: formState.ward,
                room: formState.room,
                bed_label: formState.bed_label,
                status: selectedEncounterId ? "occupied" : formState.status,
                encounter_id: selectedEncounterId,
                notes: emptyToNull(formState.notes),
              });
            }}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <ModuleField label="Sala">
                <Input
                  value={formState.ward}
                  onChange={(event) => setFormState({ ...formState, ward: event.target.value })}
                />
              </ModuleField>
              <ModuleField label="Habitacion">
                <Input
                  value={formState.room}
                  onChange={(event) => setFormState({ ...formState, room: event.target.value })}
                />
              </ModuleField>
            </div>
            <ModuleField label="Cama">
              <Input
                value={formState.bed_label}
                onChange={(event) => setFormState({ ...formState, bed_label: event.target.value })}
              />
            </ModuleField>
            <ModuleField label="Estado inicial">
              <select
                className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                value={formState.status}
                disabled={Boolean(selectedEncounterId)}
                onChange={(event) =>
                  setFormState({
                    ...formState,
                    status: event.target.value as Exclude<HospitalBedStatus, "occupied">,
                  })
                }
              >
                <option value="available">Disponible</option>
                <option value="cleaning">Limpieza</option>
                <option value="blocked">Bloqueada</option>
              </select>
            </ModuleField>
            <ModuleField label="Asignar ingreso activo">
              <select
                className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                value={formState.encounter_id}
                onChange={(event) => setFormState({ ...formState, encounter_id: event.target.value })}
              >
                <option value="">Sin asignar</option>
                {assignableHospitalizations.map((item) => (
                  <option key={item.encounter.id} value={item.encounter.id}>
                    {formatHospitalizationOption(item)}
                  </option>
                ))}
              </select>
            </ModuleField>
            <ModuleField label="Notas">
              <Textarea
                value={formState.notes}
                onChange={(event) => setFormState({ ...formState, notes: event.target.value })}
              />
            </ModuleField>
            <Button
              type="submit"
              disabled={
                mutation.isPending ||
                DEMO_MODE ||
                !canWrite ||
                !formState.ward.trim() ||
                !formState.room.trim() ||
                !formState.bed_label.trim()
              }
            >
              {mutation.isPending ? "Guardando..." : "Guardar cama"}
            </Button>
            {mutation.isError ? <p className="text-sm text-destructive">No se pudo crear la cama.</p> : null}
          </form>
        </ClinicalSectionCard>
      </div>
    </DomainModulePage>
  );
}

export function HospitalizationBoardContent({
  board,
}: {
  board: HospitalizationBoardState;
}) {
  if (board.isLoading) {
    return <LoadingRows rows={3} />;
  }
  if (board.isError) {
    return <ErrorState description="No se pudo cargar el tablero hospitalario." onRetry={board.refetch} />;
  }
  return <BedBoard items={board.items} />;
}

function ModuleField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1 text-sm font-medium">
      <span>{label}</span>
      {children}
    </label>
  );
}
