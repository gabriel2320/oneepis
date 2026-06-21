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
import { createMedication } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageMedications } from "@/lib/permissions";
import type { MedicationCreate } from "@/lib/types";

import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  fieldLabels,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function NewMedicationPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageMedications(user);
  const [formState, setFormState] = useState({ name: "", dose: "", route: "", frequency: "" });
  const mutation = useMutation({
    mutationFn: (payload: MedicationCreate) => createMedication(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/medicacion`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="medicacion">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/medicacion`} label="Medicacion" />
        <PageTitle title="Agregar medicamento" description="Medicacion activa del paciente." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar medicacion." />
        ) : null}
        <ClinicalSectionCard title="Medicamento">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                name: formState.name,
                dose: emptyToNull(formState.dose),
                route: emptyToNull(formState.route),
                frequency: emptyToNull(formState.frequency),
                started_on: new Date().toISOString().slice(0, 10),
              });
            }}
          >
            {(["name", "dose", "route", "frequency"] as const).map((field) => (
              <Field key={field} label={fieldLabels[field]}>
                <Input
                  value={formState[field]}
                  onChange={(event) => setFormState({ ...formState, [field]: event.target.value })}
                />
              </Field>
            ))}
            <Button type="submit" disabled={mutation.isPending || !formState.name.trim() || DEMO_MODE || !canWrite}>
              {mutation.isPending ? "Guardando..." : "Guardar medicamento"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}
