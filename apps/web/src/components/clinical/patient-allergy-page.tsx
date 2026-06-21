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
import { createAllergy } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageAllergies } from "@/lib/permissions";
import type { AllergyCreate } from "@/lib/types";

import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function NewAllergyPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageAllergies(user);
  const [formState, setFormState] = useState({ substance: "", reaction: "", severity: "unknown" });
  const mutation = useMutation({
    mutationFn: (payload: AllergyCreate) => createAllergy(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/alergias`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="alergias">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/alergias`} label="Alergias" />
        <PageTitle title="Agregar alergia" description="Registro puntual, auditado y reversible." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar alergias." />
        ) : null}
        <ClinicalSectionCard title="Alergia">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                substance: formState.substance,
                reaction: emptyToNull(formState.reaction),
                severity: formState.severity as AllergyCreate["severity"],
                recorded_at: new Date().toISOString(),
              });
            }}
          >
            <Field label="Sustancia">
              <Input
                value={formState.substance}
                onChange={(event) => setFormState({ ...formState, substance: event.target.value })}
              />
            </Field>
            <Field label="Reaccion">
              <Input
                value={formState.reaction}
                onChange={(event) => setFormState({ ...formState, reaction: event.target.value })}
              />
            </Field>
            <Field label="Severidad">
              <select
                className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                value={formState.severity}
                onChange={(event) => setFormState({ ...formState, severity: event.target.value })}
              >
                <option value="unknown">Desconocida</option>
                <option value="mild">Leve</option>
                <option value="moderate">Moderada</option>
                <option value="severe">Severa</option>
              </select>
            </Field>
            <Button
              type="submit"
              disabled={mutation.isPending || !formState.substance.trim() || DEMO_MODE || !canWrite}
            >
              {mutation.isPending ? "Guardando..." : "Guardar alergia"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}
