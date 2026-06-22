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
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageMedications(user);
  const [formState, setFormState] = useState({
    name: searchParams.get("name")?.slice(0, 160) ?? "",
    dose: searchParams.get("dose")?.slice(0, 80) ?? "",
    route: searchParams.get("route")?.slice(0, 80) ?? "",
    frequency: searchParams.get("frequency")?.slice(0, 120) ?? "",
    ai_action_id: searchParams.get("aiActionId")?.slice(0, 160) ?? "",
    source_text: searchParams.get("sourceText")?.slice(0, 600) ?? "",
  });
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
          {formState.ai_action_id ? (
            <div className="mb-4 rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
              <p>Formulario abierto desde AI-Chart. Revisa y edita antes de guardar.</p>
              {formState.source_text ? <p className="mt-1">Origen: {formState.source_text}</p> : null}
            </div>
          ) : null}
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
