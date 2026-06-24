"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm, useWatch } from "react-hook-form";
import { Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AppShell } from "@/components/layout/app-shell";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createClinicalInsight } from "@/lib/api/ai";
import { createClinicalEntry, listClinicalEncounters } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { demoEncounters } from "@/lib/demo-record";
import { canManageClinicalEntries, canUseClinicalAi } from "@/lib/permissions";

import {
  BackLink,
  EncounterLinkNotice,
  Field,
  PageTitle,
  SoapTextarea,
  emptyToNull,
  soapSchema,
  toDatetimeLocal,
  type SoapFormValues,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function NewSoapEntryPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWriteSoap = canManageClinicalEntries(user);
  const canUseAi = canUseClinicalAi(user);
  const [aiReview, setAiReview] = useState<string | null>(null);
  const form = useForm<SoapFormValues>({
    resolver: zodResolver(soapSchema),
    defaultValues: {
      title: "Evolucion SOAP",
      encounter_id: "",
      occurred_at: toDatetimeLocal(new Date()),
      subjective: "",
      objective: "",
      assessment: "",
      plan: "",
    },
  });
  const mutation = useMutation({
    mutationFn: (values: SoapFormValues) =>
      createClinicalEntry(patientId, {
        encounter_id: emptyToNull(values.encounter_id),
        kind: "progress",
        status: "draft",
        occurred_at: new Date(values.occurred_at).toISOString(),
        title: values.title,
        subjective: emptyToNull(values.subjective),
        objective: emptyToNull(values.objective),
        assessment: emptyToNull(values.assessment),
        plan: emptyToNull(values.plan),
        tags: ["soap"],
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/evoluciones`);
    },
  });
  const encountersQuery = useQuery({
    queryKey: ["clinical-encounters", patientId],
    queryFn: () => listClinicalEncounters(patientId),
    enabled: !DEMO_MODE,
  });
  const encounters = DEMO_MODE
    ? demoEncounters.filter((encounter) => encounter.patient_id === patientId)
    : (encountersQuery.data ?? []);
  const selectedEncounterId = useWatch({ control: form.control, name: "encounter_id" });
  const reviewMutation = useMutation({
    mutationFn: (values: SoapFormValues) =>
      createClinicalInsight({
        patient_id: patientId,
        focus: "summary",
        source_text: [
          `Titulo: ${values.title}`,
          `S: ${values.subjective || "Sin registro"}`,
          `O: ${values.objective || "Sin registro"}`,
          `A: ${values.assessment || "Sin registro"}`,
          `P: ${values.plan || "Sin registro"}`,
        ].join("\n"),
      }),
    onSuccess: (response) => {
      setAiReview(
        [
          response.summary,
          ...response.structured_points.map((point) => `- ${point}`),
          "Borrador IA - requiere revision humana.",
        ].join("\n"),
      );
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl p-4 md:p-6">
          <ErrorState description="No se pudo cargar el paciente para crear la evolucion." />
        </div>
      </AppShell>
    );
  }

  return (
    <PatientClinicalShell record={record} activeSection="evoluciones">
      <div className="space-y-5">
        <BackLink href={`/pacientes/${patientId}/evoluciones`} label="Evoluciones" />
        <PageTitle
          title="Nueva evolucion SOAP"
          description={record ? `${record.patient.first_name} ${record.patient.last_name}` : "Paciente"}
        />
        {DEMO_MODE ? <ErrorState description="El modo demo no permite guardar evoluciones reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWriteSoap ? (
          <ErrorState description="Tu rol actual no permite crear evoluciones SOAP." />
        ) : null}
        <ClinicalSectionCard
          title="SOAP"
          description="Editor amplio, sin guardado IA automatico."
          action={
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={reviewMutation.isPending || !canUseAi}
              onClick={() => reviewMutation.mutate(form.getValues())}
            >
              {canUseAi ? (reviewMutation.isPending ? "Revisando..." : "Revisar con Ollama") : "IA no permitida"}
            </Button>
          }
        >
          <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Titulo" error={form.formState.errors.title?.message}>
                <Input {...form.register("title")} />
              </Field>
              <Field label="Fecha y hora" error={form.formState.errors.occurred_at?.message}>
                <Input type="datetime-local" {...form.register("occurred_at")} />
              </Field>
            </div>
            <Field label="Encuentro">
              <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" {...form.register("encounter_id")}>
                <option value="">Sin encuentro vinculado</option>
                {encounters.map((encounter) => (
                  <option key={encounter.id} value={encounter.id}>
                    {encounter.reason} - {encounter.type}
                  </option>
                ))}
              </select>
            </Field>
            <EncounterLinkNotice
              hasEncounters={encounters.length > 0}
              hasSelectedEncounter={Boolean(selectedEncounterId)}
            />
            <SoapTextarea label="Subjetivo" registration={form.register("subjective")} />
            <SoapTextarea label="Objetivo" registration={form.register("objective")} />
            <SoapTextarea label="Analisis" registration={form.register("assessment")} />
            <SoapTextarea label="Plan" registration={form.register("plan")} />
            <Button type="submit" disabled={mutation.isPending || DEMO_MODE || !canWriteSoap}>
              <Save className="h-4 w-4" />
              {mutation.isPending ? "Guardando..." : "Guardar borrador"}
            </Button>
            {mutation.isError ? <p className="text-sm text-destructive">No se pudo guardar.</p> : null}
          </form>
        </ClinicalSectionCard>
        {reviewMutation.isError ? (
          <ErrorState description="Ollama no pudo revisar el borrador. La evolucion sigue editable." />
        ) : null}
        {aiReview ? (
          <ClinicalSectionCard title="Revision Ollama" description="Borrador IA - requiere revision humana.">
            <pre className="whitespace-pre-wrap rounded-md border bg-muted/40 p-3 text-sm">{aiReview}</pre>
          </ClinicalSectionCard>
        ) : null}
      </div>
    </PatientClinicalShell>
  );
}
