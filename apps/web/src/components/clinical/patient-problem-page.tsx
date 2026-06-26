"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createActiveProblem } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageProblems } from "@/lib/permissions";
import type { ActiveProblemCreate } from "@/lib/types";

import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function NewProblemPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageProblems(user);
  const [formState, setFormState] = useState({
    title: searchParams.get("title")?.slice(0, 160) ?? "",
    code_system: "",
    code: "",
    onset_date: "",
    notes: searchParams.get("notes")?.slice(0, 1200) ?? "",
    ai_action_id: searchParams.get("aiActionId")?.slice(0, 160) ?? "",
  });
  const mutation = useMutation({
    mutationFn: (payload: ActiveProblemCreate) => createActiveProblem(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
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
        <PageTitle title="Agregar antecedente activo" description="Dato longitudinal usado como contexto clinico." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar antecedentes activos." />
        ) : null}
        <ClinicalSectionCard title="Antecedente clinico">
          {formState.ai_action_id ? (
            <div className="mb-4 rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
              Formulario prellenado desde AI-Chart. Revisa y edita antes de guardar.
            </div>
          ) : null}
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                title: formState.title,
                code_system: emptyToNull(formState.code_system),
                code: emptyToNull(formState.code),
                onset_date: emptyToNull(formState.onset_date),
                notes: emptyToNull(formState.notes),
              });
            }}
          >
            <Field label="Problema">
              <Input
                value={formState.title}
                onChange={(event) => setFormState({ ...formState, title: event.target.value })}
              />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Sistema codigo">
                <Input
                  value={formState.code_system}
                  onChange={(event) => setFormState({ ...formState, code_system: event.target.value })}
                />
              </Field>
              <Field label="Codigo">
                <Input
                  value={formState.code}
                  onChange={(event) => setFormState({ ...formState, code: event.target.value })}
                />
              </Field>
            </div>
            <Field label="Inicio">
              <Input
                type="date"
                value={formState.onset_date}
                onChange={(event) => setFormState({ ...formState, onset_date: event.target.value })}
              />
            </Field>
            <Field label="Notas">
              <Textarea
                value={formState.notes}
                onChange={(event) => setFormState({ ...formState, notes: event.target.value })}
              />
            </Field>
            <Button type="submit" disabled={mutation.isPending || DEMO_MODE || !canWrite || !formState.title.trim()}>
              {mutation.isPending ? "Guardando..." : "Guardar problema"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}
