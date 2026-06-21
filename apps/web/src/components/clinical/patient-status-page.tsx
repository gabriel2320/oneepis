"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { DEMO_MODE } from "@/lib/api/client";
import { updatePatient } from "@/lib/api/patients";
import { canManagePatient } from "@/lib/permissions";
import type { CareContext, PatientClinicalStatus, PatientRecordSnapshot } from "@/lib/types";

import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  careContextOptions,
  clinicalStatusOptions,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function EditPatientStatusPage() {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManagePatient(user);

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
        <PageTitle title="Estado clinico" description="Estado de ficha y contexto asistencial actual." />
        {DEMO_MODE ? <ErrorState description="El modo demo no permite modificar estado clinico real." /> : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite modificar el estado de ficha." />
        ) : null}
        <ClinicalSectionCard title="Estado y contexto">
          <PatientStatusForm patientId={patientId} record={record} canWrite={canWrite} />
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}

function PatientStatusForm({
  patientId,
  record,
  canWrite,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  canWrite: boolean;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<{
    clinical_status: PatientClinicalStatus;
    current_care_context: CareContext;
  }>({
    clinical_status: record.patient.clinical_status,
    current_care_context: record.patient.current_care_context,
  });
  const mutation = useMutation({
    mutationFn: () => updatePatient(patientId, formState),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      router.push(`/pacientes/${patientId}/ficha`);
    },
  });

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      <Field label="Estado ficha">
        <select
          className="h-9 w-full rounded-md border bg-background px-3 text-sm"
          value={formState.clinical_status}
          onChange={(event) =>
            setFormState({
              ...formState,
              clinical_status: event.target.value as PatientClinicalStatus,
            })
          }
        >
          {clinicalStatusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Contexto asistencial">
        <select
          className="h-9 w-full rounded-md border bg-background px-3 text-sm"
          value={formState.current_care_context}
          onChange={(event) =>
            setFormState({
              ...formState,
              current_care_context: event.target.value as CareContext,
            })
          }
        >
          {careContextOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>
      <Button type="submit" disabled={mutation.isPending || DEMO_MODE || !canWrite}>
        {mutation.isPending ? "Guardando..." : "Guardar estado"}
      </Button>
      {mutation.isError ? <p className="text-sm text-destructive">No se pudo actualizar el estado.</p> : null}
    </form>
  );
}
