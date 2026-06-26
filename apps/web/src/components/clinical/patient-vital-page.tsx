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
import { createVitalSign } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { canRecordVitals } from "@/lib/permissions";
import type { VitalSignCreate } from "@/lib/types";

import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  fieldLabels,
  numberOrNull,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function NewVitalSignPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canRecordVitals(user);
  const [formState, setFormState] = useState({
    systolic_bp: "",
    diastolic_bp: "",
    heart_rate_bpm: "",
    oxygen_saturation_pct: "",
    temperature_c: "",
    ai_action_id: searchParams.get("aiActionId")?.slice(0, 160) ?? "",
    source_text: searchParams.get("sourceText")?.slice(0, 600) ?? "",
  });
  const mutation = useMutation({
    mutationFn: (payload: VitalSignCreate) => createVitalSign(patientId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["vital-signs", patientId] }),
      ]);
      router.push(`/pacientes/${patientId}/signos-vitales`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="signos-vitales">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/signos-vitales`} label="Signos vitales" />
        <PageTitle title="Registrar signos vitales" description="Control puntual del paciente." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu perfil no tiene permiso para registrar signos vitales." />
        ) : null}
        <ClinicalSectionCard title="Control">
          {formState.ai_action_id ? (
            <div className="mb-4 rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
              <p>Formulario abierto desde AI-Chart. Ingresa o corrige los valores antes de guardar.</p>
              {formState.source_text ? <p className="mt-1">Origen: {formState.source_text}</p> : null}
            </div>
          ) : null}
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({
                measured_at: new Date().toISOString(),
                systolic_bp: numberOrNull(formState.systolic_bp),
                diastolic_bp: numberOrNull(formState.diastolic_bp),
                heart_rate_bpm: numberOrNull(formState.heart_rate_bpm),
                oxygen_saturation_pct: emptyToNull(formState.oxygen_saturation_pct),
                temperature_c: emptyToNull(formState.temperature_c),
              });
            }}
          >
            {(["systolic_bp", "diastolic_bp", "heart_rate_bpm", "oxygen_saturation_pct", "temperature_c"] as const).map(
              (field) => (
                <Field key={field} label={fieldLabels[field]}>
                  <Input
                    inputMode="decimal"
                    value={formState[field]}
                    onChange={(event) => setFormState({ ...formState, [field]: event.target.value })}
                  />
                </Field>
              ),
            )}
            <Button type="submit" disabled={mutation.isPending || DEMO_MODE || !canWrite}>
              {mutation.isPending ? "Guardando..." : "Guardar signos"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}
