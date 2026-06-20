"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useState } from "react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { ModulePage } from "@/components/clinical/module-pages";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { BedBoard, DailySheet, RoundList } from "@/components/clinical/widgets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { DEMO_MODE } from "@/lib/api/client";
import {
  createHospitalBed,
  listActiveHospitalizations,
  listHospitalBeds,
  updateHospitalBed,
} from "@/lib/api/hospitalization";
import { demoEncounters, demoHospitalBeds, demoRecords } from "@/lib/demo-record";
import { canManageEncounters } from "@/lib/permissions";
import type {
  HospitalBedCreate,
  HospitalBedStatus,
  HospitalizationBoardItem,
} from "@/lib/types";

export function HospitalHomePage() {
  const board = useHospitalizationBoard();

  return (
    <ModulePage
      title="Hospitalizacion"
      description="Base para camas, rondas, hoja diaria e indicaciones."
      actions={[
        { href: "/hospitalizacion/camas", label: "Camas" },
        { href: "/hospitalizacion/rondas", label: "Rondas" },
      ]}
    >
      <div className="grid gap-4 xl:grid-cols-2">
        <ClinicalSectionCard title="Camas">
          <HospitalizationBoardContent board={board} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Rondas">
          <RoundList />
        </ClinicalSectionCard>
      </div>
    </ModulePage>
  );
}

export function HospitalBedsPage() {
  const board = useHospitalizationBoard();
  const beds = useHospitalBeds();

  return (
    <ModulePage
      title="Camas"
      description="Tablero hospitalario desde encuentros activos."
      actions={[{ href: "/hospitalizacion/camas/nueva", label: "Nueva cama" }]}
    >
      <div className="space-y-4">
        <ClinicalSectionCard title="Pacientes hospitalizados">
          <HospitalizationBoardContent board={board} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Administracion de camas">
          <HospitalBedAdminContent beds={beds} board={board} />
        </ClinicalSectionCard>
      </div>
    </ModulePage>
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
    <ModulePage title="Nueva cama" description="Cama hospitalaria estructurada y auditada.">
      <div className="max-w-xl space-y-5">
        <Button asChild variant="outline" size="sm">
          <Link href="/hospitalizacion/camas">Volver a camas</Link>
        </Button>
        {DEMO_MODE ? <ErrorState description="El modo demo no permite crear camas reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite administrar camas." />
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
    </ModulePage>
  );
}

export function HospitalRoundsPage() {
  return (
    <ModulePage title="Rondas" description="Lista de rondas para pacientes hospitalizados.">
      <ClinicalSectionCard title="RoundList">
        <RoundList />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function DailySheetPage() {
  return (
    <ModulePage title="Hoja diaria" description="Pantalla hospitalizada por paciente.">
      <ClinicalSectionCard title="DailySheet">
        <DailySheet />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function OrdersPage() {
  return (
    <ModulePage title="Indicaciones" description="Base para indicaciones hospitalarias auditadas.">
      <ClinicalSectionCard title="Indicaciones">
        <EmptyState title="Indicaciones pendientes" description="Requiere permisos y firma clinica." />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

function HospitalizationBoardContent({
  board,
}: {
  board: ReturnType<typeof useHospitalizationBoard>;
}) {
  if (board.isLoading) {
    return <LoadingRows rows={3} />;
  }
  if (board.isError) {
    return <ErrorState description="No se pudo cargar el tablero hospitalario." onRetry={board.refetch} />;
  }
  return <BedBoard items={board.items} />;
}

function HospitalBedAdminContent({
  beds,
  board,
}: {
  beds: ReturnType<typeof useHospitalBeds>;
  board: ReturnType<typeof useHospitalizationBoard>;
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

function useHospitalizationBoard() {
  const boardQuery = useQuery({
    queryKey: ["hospitalization-board"],
    queryFn: listActiveHospitalizations,
    enabled: !DEMO_MODE,
  });
  const demoItems = DEMO_MODE ? getDemoHospitalizations() : [];
  return {
    items: DEMO_MODE ? demoItems : (boardQuery.data ?? []),
    isLoading: !DEMO_MODE && boardQuery.isLoading,
    isError: !DEMO_MODE && boardQuery.isError,
    refetch: () => {
      void boardQuery.refetch();
    },
  };
}

function useHospitalBeds() {
  const bedsQuery = useQuery({
    queryKey: ["hospital-beds"],
    queryFn: listHospitalBeds,
    enabled: !DEMO_MODE,
  });
  return {
    items: DEMO_MODE ? demoHospitalBeds : (bedsQuery.data ?? []),
    isLoading: !DEMO_MODE && bedsQuery.isLoading,
    isError: !DEMO_MODE && bedsQuery.isError,
    refetch: () => {
      void bedsQuery.refetch();
    },
  };
}

function getDemoHospitalizations(): HospitalizationBoardItem[] {
  return demoEncounters
    .filter((encounter) => encounter.type === "hospitalization" && encounter.status === "in_progress")
    .flatMap((encounter) => {
      const record = demoRecords.find((item) => item.patient.id === encounter.patient_id);
      const bed = demoHospitalBeds.find((item) => item.encounter_id === encounter.id) ?? null;
      return record ? [{ patient: record.patient, encounter, bed }] : [];
    });
}

function ModuleField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1 text-sm font-medium">
      <span>{label}</span>
      {children}
    </label>
  );
}

function formatBedLabel(bed: { ward: string; room: string; bed_label: string }) {
  return `${bed.ward} / ${bed.room} / Cama ${bed.bed_label}`;
}

function formatHospitalizationOption(item: HospitalizationBoardItem) {
  return `${item.patient.first_name} ${item.patient.last_name} - ${item.encounter.reason}`;
}

function emptyToNull(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

const hospitalBedStatusLabel: Record<HospitalBedStatus, string> = {
  available: "Disponible",
  occupied: "Ocupada",
  cleaning: "Limpieza",
  blocked: "Bloqueada",
};

const hospitalBedTransitionOptions: { value: Exclude<HospitalBedStatus, "occupied">; label: string }[] = [
  { value: "available", label: "Disponible" },
  { value: "cleaning", label: "Limpieza" },
  { value: "blocked", label: "Bloquear" },
];
