"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AlertCard, ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createMedication } from "@/lib/api/clinical-record";
import { validateMedicationDraft } from "@/lib/api/medication";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageMedications } from "@/lib/permissions";
import type { MedicationCreate, MedicationDraftValidationResponse } from "@/lib/types";

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
    catalog_item_id: searchParams.get("catalogItemId")?.slice(0, 80) ?? "",
    name: searchParams.get("name")?.slice(0, 160) ?? "",
    dose: searchParams.get("dose")?.slice(0, 80) ?? "",
    route: searchParams.get("route")?.slice(0, 80) ?? "",
    frequency: searchParams.get("frequency")?.slice(0, 120) ?? "",
    dose_override_reason: "",
    ai_action_id: searchParams.get("aiActionId")?.slice(0, 160) ?? "",
    source_text: searchParams.get("sourceText")?.slice(0, 600) ?? "",
  });
  const [validation, setValidation] = useState<MedicationDraftValidationResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const validationMutation = useMutation({
    mutationFn: (payload: MedicationCreate) =>
      validateMedicationDraft(patientId, {
        catalog_item_id: payload.catalog_item_id,
        name: payload.name,
        dose: payload.dose,
        route: payload.route,
        frequency: payload.frequency,
      }),
    onSuccess: setValidation,
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
          <ErrorState description="Tu perfil no tiene permiso para registrar medicacion." />
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
            onSubmit={async (event) => {
              event.preventDefault();
              setSubmitError(null);
              const payload: MedicationCreate = {
                catalog_item_id: emptyToNull(formState.catalog_item_id),
                name: formState.name,
                dose: emptyToNull(formState.dose),
                route: emptyToNull(formState.route),
                frequency: emptyToNull(formState.frequency),
                started_on: new Date().toISOString().slice(0, 10),
                dose_override_reason: emptyToNull(formState.dose_override_reason),
              };
              try {
                const result = await validationMutation.mutateAsync(payload);
                if (result.blocking && !formState.dose_override_reason.trim()) {
                  return;
                }
                await mutation.mutateAsync(payload);
              } catch (error) {
                setSubmitError(error instanceof Error ? error.message : "No se pudo guardar.");
              }
            }}
          >
            {formState.catalog_item_id ? (
              <div className="rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">Vademecum</Badge>{" "}
                  <span>Medicamento seleccionado desde catalogo local curado.</span>
                </div>
              </div>
            ) : null}
            {(["name", "dose", "route", "frequency"] as const).map((field) => (
              <Field key={field} label={fieldLabels[field]}>
                <Input
                  value={formState[field]}
                  onChange={(event) => setFormState({ ...formState, [field]: event.target.value })}
                />
              </Field>
            ))}
            {validation ? <MedicationDoseValidationPanel validation={validation} /> : null}
            {validation?.blocking ? (
              <Field label="Justificacion de override">
                <Textarea
                  value={formState.dose_override_reason}
                  onChange={(event) =>
                    setFormState({ ...formState, dose_override_reason: event.target.value })
                  }
                  placeholder="Motivo clinico para guardar pese a la alerta."
                />
              </Field>
            ) : null}
            {submitError ? <ErrorState description={submitError} /> : null}
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={validationMutation.isPending || !formState.name.trim() || DEMO_MODE}
                onClick={() =>
                  validationMutation.mutate({
                    catalog_item_id: emptyToNull(formState.catalog_item_id),
                    name: formState.name,
                    dose: emptyToNull(formState.dose),
                    route: emptyToNull(formState.route),
                    frequency: emptyToNull(formState.frequency),
                  })
                }
              >
                {validationMutation.isPending ? "Validando..." : "Validar dosis"}
              </Button>
              <Button
                type="submit"
                disabled={mutation.isPending || !formState.name.trim() || DEMO_MODE || !canWrite}
              >
                {mutation.isPending ? "Guardando..." : "Guardar medicamento"}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              No crea receta valida, orden ejecutable, firma ni folio.
            </p>
          </form>
        </ClinicalSectionCard>
      </div>
    </PatientClinicalShell>
  );
}

function MedicationDoseValidationPanel({
  validation,
}: {
  validation: MedicationDraftValidationResponse;
}) {
  const tone = validation.blocking ? "danger" : "info";
  return (
    <AlertCard title={validation.blocking ? "Alerta de dosis" : "Validacion de dosis"} tone={tone}>
      {validation.warnings.length ? (
        <div className="space-y-2">
          {validation.warnings.map((warning) => (
            <div key={`${warning.severity}-${warning.message}`}>
              <Badge variant={warning.severity === "critical" ? "warning" : "outline"}>
                {warning.severity}
              </Badge>
              <p className="mt-1">{warning.message}</p>
              {warning.source ? (
                <p className="mt-1 text-xs">Fuente: {warning.source.source_label}</p>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <p>No se detectaron alertas bloqueantes con las reglas disponibles.</p>
      )}
      {validation.limitations.length ? (
        <ul className="mt-2 list-disc space-y-1 pl-4 text-xs">
          {validation.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </AlertCard>
  );
}
