"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AppShell } from "@/components/layout/app-shell";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createClinicalInsight } from "@/lib/api/ai";
import { createClinicalEntry, createClinicalEncounter, listClinicalEncounters } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { updatePatient } from "@/lib/api/patients";
import { demoEncounters } from "@/lib/demo-record";
import {
  canManageClinicalEntries,
  canManageEncounters,
  canManagePatient,
  canUseClinicalAi,
} from "@/lib/permissions";
import type {
  CareContext,
  ClinicalEncounterCreate,
  EncounterStatus,
  EncounterType,
  PatientClinicalStatus,
  PatientRecordSnapshot,
} from "@/lib/types";
import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  SoapTextarea,
  careContextOptions,
  clinicalStatusOptions,
  emptyToNull,
  encounterStatusOptions,
  encounterTypeOptions,
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
        {DEMO_MODE ? (
          <ErrorState description="El modo demo no permite guardar evoluciones reales." />
        ) : null}
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
        {DEMO_MODE ? (
          <ErrorState description="El modo demo no permite modificar estado clinico real." />
        ) : null}
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
      router.push(`/pacientes/${patientId}/encuentros`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="encuentros">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/encuentros`} label="Encuentros" />
        <PageTitle title="Nuevo encuentro" description="Consulta, ingreso o atencion ligada al paciente." />
        {DEMO_MODE ? (
          <ErrorState description="El modo demo no permite crear encuentros reales." />
        ) : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite crear encuentros clinicos." />
        ) : null}
        <ClinicalSectionCard title="Encuentro">
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

export { NewAllergyPage, NewMedicationPage, NewProblemPage, NewVitalSignPage } from "./patient-entity-write-pages";
