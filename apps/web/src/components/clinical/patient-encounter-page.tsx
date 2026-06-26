"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createClinicalEncounter } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageEncounters } from "@/lib/permissions";
import type { ClinicalEncounterCreate, EncounterStatus, EncounterType } from "@/lib/types";

import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  encounterStatusOptions,
  encounterTypeOptions,
  toDatetimeLocal,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function NewEncounterPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageEncounters(user);
  const [formState, setFormState] = useState({
    type: "ambulatory" as EncounterType,
    status: "in_progress" as EncounterStatus,
    reason: "",
    started_at: toDatetimeLocal(new Date()),
    ended_at: "",
    location_label: "",
    notes: "",
  });
  const mutation = useMutation({
    mutationFn: (payload: ClinicalEncounterCreate) => createClinicalEncounter(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["clinical-encounters", patientId] });
      router.push(`/pacientes/${patientId}/ficha`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="ficha">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/ficha`} label="Ficha" />
        <PageTitle title="Registrar atencion o ingreso" description="Dato de soporte para vincular evoluciones, hospitalizacion o atencion ambulatoria." />
        {DEMO_MODE ? <ErrorState description="El modo demo no permite crear datos de soporte reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar atenciones o ingresos." />
        ) : null}
        <ClinicalSectionCard title="Dato de soporte">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                type: formState.type,
                status: formState.status,
                reason: formState.reason,
                started_at: new Date(formState.started_at).toISOString(),
                ended_at: formState.ended_at ? new Date(formState.ended_at).toISOString() : null,
                location_label: emptyToNull(formState.location_label),
                notes: emptyToNull(formState.notes),
              });
            }}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Tipo">
                <select
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                  value={formState.type}
                  onChange={(event) =>
                    setFormState({ ...formState, type: event.target.value as EncounterType })
                  }
                >
                  {encounterTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Estado">
                <select
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                  value={formState.status}
                  onChange={(event) =>
                    setFormState({ ...formState, status: event.target.value as EncounterStatus })
                  }
                >
                  {encounterStatusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <Field label="Motivo">
              <Input
                value={formState.reason}
                onChange={(event) => setFormState({ ...formState, reason: event.target.value })}
              />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Inicio">
                <Input
                  type="datetime-local"
                  value={formState.started_at}
                  onChange={(event) => setFormState({ ...formState, started_at: event.target.value })}
                />
              </Field>
              <Field label="Cierre">
                <Input
                  type="datetime-local"
                  value={formState.ended_at}
                  onChange={(event) => setFormState({ ...formState, ended_at: event.target.value })}
                />
              </Field>
            </div>
            <Field label="Ubicacion">
              <Input
                value={formState.location_label}
                onChange={(event) => setFormState({ ...formState, location_label: event.target.value })}
              />
            </Field>
            <Field label="Notas">
              <Textarea
                value={formState.notes}
                onChange={(event) => setFormState({ ...formState, notes: event.target.value })}
              />
            </Field>
            <Button
              type="submit"
              disabled={
                mutation.isPending ||
                DEMO_MODE ||
                !canWrite ||
                !formState.reason.trim() ||
                !formState.started_at.trim()
              }
            >
              {mutation.isPending ? "Guardando..." : "Guardar encuentro"}
            </Button>
            {mutation.isError ? <p className="text-sm text-destructive">No se pudo crear el encuentro.</p> : null}
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}
