"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm, type UseFormRegisterReturn } from "react-hook-form";
import { z } from "zod";
import { ArrowLeft, Plus, Save, Search } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AppShell } from "@/components/layout/app-shell";
import { AiInsightPanel } from "@/components/clinical-record/ai-insight-panel";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import {
  PatientClinicalLoading,
  PatientClinicalShell,
} from "@/components/clinical/patient-clinical-shell";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import {
  AiSafetyPanel,
  AllergyList,
  AuditTimeline,
  ClinicalTimeline,
  CriticalAlerts,
  EncounterList,
  LatestVitalsTrend,
  MedicationList,
  PatientLongitudinalSummary,
  ProblemList,
  QuickSoapEditor,
  VitalsStrip,
} from "@/components/clinical/widgets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createClinicalInsight, createPatientAiSuggestions } from "@/lib/api/ai";
import {
  createAllergy,
  createActiveProblem,
  createClinicalEntry,
  createClinicalEncounter,
  createMedication,
  createVitalSign,
  listClinicalEncounters,
  listAuditEvents,
  listVitalSigns,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { createPatient, getPatientRecord, listPatients, updatePatient } from "@/lib/api/patients";
import { demoEncounters, demoRecords } from "@/lib/demo-record";
import {
  canCreatePatient,
  canManagePatient,
  canManageAllergies,
  canManageClinicalEntries,
  canManageMedications,
  canManageProblems,
  canManageEncounters,
  canRecordVitals,
  canUseClinicalAi,
} from "@/lib/permissions";
import type {
  AllergyCreate,
  ActiveProblemCreate,
  AuthUser,
  CareContext,
  ClinicalEncounterCreate,
  EncounterStatus,
  EncounterType,
  MedicationCreate,
  Patient,
  PatientAiSuggestionsResponse,
  PatientClinicalStatus,
  PatientCreate,
  PatientRecordSnapshot,
  VitalSignCreate,
} from "@/lib/types";
import type { ReactNode } from "react";

const patientSchema = z.object({
  first_name: z.string().min(1, "Nombre requerido"),
  last_name: z.string().min(1, "Apellido requerido"),
  preferred_name: z.string().optional(),
  birth_date: z.string().min(1, "Fecha requerida"),
  sex_at_birth: z.enum(["female", "male", "intersex", "unknown"]),
  clinical_identifier: z.string().optional(),
  contact_phone: z.string().optional(),
  email: z.string().email("Email invalido").optional().or(z.literal("")),
});

type PatientFormValues = z.infer<typeof patientSchema>;

const soapSchema = z.object({
  title: z.string().min(1, "Titulo requerido"),
  occurred_at: z.string().min(1, "Fecha requerida"),
  subjective: z.string().optional(),
  objective: z.string().optional(),
  assessment: z.string().optional(),
  plan: z.string().optional(),
});

type SoapFormValues = z.infer<typeof soapSchema>;

const encounterTypeOptions: { value: EncounterType; label: string }[] = [
  { value: "ambulatory", label: "Ambulatorio" },
  { value: "hospitalization", label: "Hospitalizacion" },
  { value: "emergency", label: "Urgencia" },
  { value: "unknown", label: "No definido" },
];

const encounterStatusOptions: { value: EncounterStatus; label: string }[] = [
  { value: "scheduled", label: "Programado" },
  { value: "in_progress", label: "En curso" },
  { value: "completed", label: "Completado" },
  { value: "cancelled", label: "Cancelado" },
];

const clinicalStatusOptions: { value: PatientClinicalStatus; label: string }[] = [
  { value: "draft", label: "Borrador" },
  { value: "active", label: "Activa" },
  { value: "closed", label: "Cerrada" },
  { value: "archived", label: "Archivada" },
];

const careContextOptions: { value: CareContext; label: string }[] = [
  { value: "unknown", label: "No definido" },
  { value: "ambulatory", label: "Ambulatorio" },
  { value: "hospitalized", label: "Hospitalizado" },
];

type PatientSection =
  | "ficha"
  | "encuentros"
  | "evoluciones"
  | "problemas"
  | "alergias"
  | "medicacion"
  | "signos-vitales"
  | "documentos"
  | "ia"
  | "auditoria";

export function PatientsIndexPage() {
  const [search, setSearch] = useState("");
  const { user, isLoading: userLoading } = useCurrentUser();
  const canCreate = canCreatePatient(user);
  const patientQuery = useQuery({
    queryKey: ["patients", search],
    queryFn: () => listPatients(search),
    enabled: !DEMO_MODE,
  });
  const patients = DEMO_MODE ? demoRecords.map((item) => item.patient) : patientQuery.data;

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-5 p-4 md:p-6">
        <PageTitle
          title="Pacientes"
          description="Ficha clinica persistente, auditable y lista para trabajo E2E."
          action={
            canCreate ? (
              <Button asChild>
                <Link href="/pacientes/nuevo">
                  <Plus className="h-4 w-4" />
                  Nuevo
                </Link>
              </Button>
            ) : (
              <NoPermissionButton label={userLoading ? "Cargando rol" : "Sin permiso"} />
            )
          }
        />

        <div className="relative max-w-xl" data-print-hidden="true">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar por nombre o identificador"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {patientQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={4} /> : null}
        {patientQuery.isError && !DEMO_MODE ? (
          <ErrorState
            description="Verifica que FastAPI este corriendo y que PostgreSQL este disponible."
            onRetry={() => patientQuery.refetch()}
          />
        ) : null}
        {patients && patients.length === 0 ? (
          <EmptyState
            title="Sin pacientes"
            description="Crea el primer registro para probar el flujo paciente -> ficha -> auditoria."
            action={
              canCreate ? (
                <Button asChild>
                  <Link href="/pacientes/nuevo">Crear paciente</Link>
                </Button>
              ) : (
                <NoPermissionButton label="Sin permiso" />
              )
            }
          />
        ) : null}
        {patients && patients.length > 0 ? <PatientList patients={patients} /> : null}
      </div>
    </AppShell>
  );
}

export function NewPatientPage() {
  const router = useRouter();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canCreate = canCreatePatient(user);
  const form = useForm<PatientFormValues>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      preferred_name: "",
      birth_date: "",
      sex_at_birth: "unknown",
      clinical_identifier: "",
      contact_phone: "",
      email: "",
    },
  });
  const createMutation = useMutation({
    mutationFn: (payload: PatientCreate) => createPatient(payload),
    onSuccess: (patient) => router.push(`/pacientes/${patient.id}/ficha`),
  });

  function handleSubmit(values: PatientFormValues) {
    createMutation.mutate({
      first_name: values.first_name,
      last_name: values.last_name,
      preferred_name: emptyToNull(values.preferred_name),
      birth_date: values.birth_date,
      sex_at_birth: values.sex_at_birth,
      clinical_identifier: emptyToNull(values.clinical_identifier),
      contact_phone: emptyToNull(values.contact_phone),
      email: emptyToNull(values.email),
      emergency_contact: {},
    });
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-5 p-4 md:p-6">
        <BackLink href="/pacientes" label="Pacientes" />
        <PageTitle title="Nuevo paciente" description="Registro minimo para abrir ficha clinica." />
        {DEMO_MODE ? (
          <ErrorState description="El modo demo esta activo. Desactiva NEXT_PUBLIC_DEMO_MODE para escribir en API." />
        ) : null}
        {!DEMO_MODE && !userLoading && !canCreate ? (
          <ErrorState description="Tu rol actual no permite crear fichas de paciente." />
        ) : null}
        <ClinicalSectionCard title="Identificacion">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit(handleSubmit)}>
            <Field label="Nombre" error={form.formState.errors.first_name?.message}>
              <Input {...form.register("first_name")} autoComplete="off" />
            </Field>
            <Field label="Apellido" error={form.formState.errors.last_name?.message}>
              <Input {...form.register("last_name")} autoComplete="off" />
            </Field>
            <Field label="Nombre social">
              <Input {...form.register("preferred_name")} autoComplete="off" />
            </Field>
            <Field label="Fecha nacimiento" error={form.formState.errors.birth_date?.message}>
              <Input type="date" {...form.register("birth_date")} />
            </Field>
            <Field label="Sexo registrado">
              <select className="h-9 rounded-md border bg-background px-3 text-sm" {...form.register("sex_at_birth")}>
                <option value="unknown">No informado</option>
                <option value="female">Femenino</option>
                <option value="male">Masculino</option>
                <option value="intersex">Intersex</option>
              </select>
            </Field>
            <Field label="Identificador clinico">
              <Input {...form.register("clinical_identifier")} autoComplete="off" />
            </Field>
            <Field label="Telefono">
              <Input {...form.register("contact_phone")} autoComplete="off" />
            </Field>
            <Field label="Email" error={form.formState.errors.email?.message}>
              <Input {...form.register("email")} autoComplete="off" />
            </Field>
            <div className="md:col-span-2">
              <Button type="submit" disabled={createMutation.isPending || DEMO_MODE || !canCreate}>
                <Save className="h-4 w-4" />
                {createMutation.isPending ? "Guardando..." : "Crear ficha"}
              </Button>
              {createMutation.isError ? (
                <p className="mt-3 text-sm text-destructive">No se pudo crear el paciente.</p>
              ) : null}
            </div>
          </form>
        </ClinicalSectionCard>
      </div>
    </AppShell>
  );
}

export function PatientRecordScreen({ section = "ficha" }: { section?: PatientSection }) {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (recordQuery.isError && !DEMO_MODE) {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl p-4 md:p-6">
          <ErrorState
            description="No se pudo cargar la ficha del paciente."
            onRetry={() => recordQuery.refetch()}
          />
        </div>
      </AppShell>
    );
  }

  if (!record) {
    return <PatientClinicalLoading />;
  }

  return (
    <PatientClinicalShell record={record} activeSection={section}>
      <PatientSectionContent record={record} section={section} patientId={patientId} />
    </PatientClinicalShell>
  );
}

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

function PatientSectionContent({
  record,
  section,
  patientId,
}: {
  record: PatientRecordSnapshot;
  section: PatientSection;
  patientId: string;
}) {
  const { user } = useCurrentUser();
  const canWriteSoap = canManageClinicalEntries(user);
  const canUseAi = canUseClinicalAi(user);
  const canEditPatient = canManagePatient(user);

  if (section === "ficha") {
    return (
      <div className="space-y-4">
        <CriticalAlerts record={record} />
        <VitalsStrip vital={record.latest_vitals} />
        <div className="flex justify-end" data-print-hidden="true">
          {canEditPatient ? (
            <Button asChild variant="outline" size="sm">
              <Link href={`/pacientes/${patientId}/estado`}>Editar estado</Link>
            </Button>
          ) : (
            <NoPermissionButton label="Estado bloqueado" />
          )}
        </div>
        <PatientLongitudinalSummary record={record} />
        <div className="grid gap-4 xl:grid-cols-[1fr_380px]">
          <ClinicalSectionCard
            title="Linea clinica"
            action={
              canWriteSoap ? (
                <QuickSoapEditor href={`/pacientes/${patientId}/evoluciones/nueva`} />
              ) : (
                <NoPermissionButton label="SOAP no permitido" />
              )
            }
          >
            <ClinicalTimeline entries={record.recent_entries} />
          </ClinicalSectionCard>
          <div className="space-y-4">
            <ClinicalSectionCard title="Alergias">
              <AllergyList allergies={record.active_allergies} />
            </ClinicalSectionCard>
            <ClinicalSectionCard title="Medicacion activa">
              <MedicationList medications={record.active_medications} />
            </ClinicalSectionCard>
            <PatientAiSuggestionsPanel patientId={patientId} canUseAi={canUseAi} />
          </div>
        </div>
      </div>
    );
  }

  if (section === "evoluciones") {
    return (
      <ClinicalSectionCard
        title="Evoluciones"
        action={
          canWriteSoap ? (
            <QuickSoapEditor href={`/pacientes/${patientId}/evoluciones/nueva`} />
          ) : (
            <NoPermissionButton label="SOAP no permitido" />
          )
        }
      >
        <ClinicalTimeline entries={record.recent_entries} />
      </ClinicalSectionCard>
    );
  }

  if (section === "encuentros") {
    return <EncounterWorkspace patientId={patientId} user={user} />;
  }

  if (section === "alergias") {
    return <AllergyWorkspace patientId={patientId} record={record} user={user} />;
  }

  if (section === "medicacion") {
    return <MedicationWorkspace patientId={patientId} record={record} user={user} />;
  }

  if (section === "signos-vitales") {
    return <VitalsWorkspace patientId={patientId} record={record} user={user} />;
  }

  if (section === "ia") {
    if (!canUseAi) {
      return (
        <ClinicalSectionCard title="IA clinica">
          <EmptyState
            title="IA no permitida para este rol"
            description="Las sugerencias clinicas quedan disponibles para medico, admin o dev."
          />
        </ClinicalSectionCard>
      );
    }
    return (
      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <AiInsightPanel />
        <AiSafetyPanel />
      </div>
    );
  }

  if (section === "auditoria") {
    return <AuditWorkspace patientId={patientId} />;
  }

  if (section === "problemas") {
    return <ProblemWorkspace patientId={patientId} record={record} user={user} />;
  }

  return (
    <ClinicalSectionCard title="Documentos">
      <EmptyState
        title="Documentos sin uploads reales"
        description="Se habilitara cuando existan autenticacion, permisos y politica PHI."
      />
    </ClinicalSectionCard>
  );
}

function EncounterWorkspace({ patientId, user }: { patientId: string; user: AuthUser | null }) {
  const canWrite = canManageEncounters(user);
  const encountersQuery = useQuery({
    queryKey: ["clinical-encounters", patientId],
    queryFn: () => listClinicalEncounters(patientId),
    enabled: !DEMO_MODE,
  });
  const encounters = DEMO_MODE
    ? demoEncounters.filter((encounter) => encounter.patient_id === patientId)
    : encountersQuery.data;

  return (
    <ClinicalSectionCard
      title="Encuentros"
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/encuentros/nuevo`}>Nuevo</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      {encountersQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
      {encountersQuery.isError && !DEMO_MODE ? (
        <ErrorState description="No se pudieron cargar los encuentros." onRetry={() => encountersQuery.refetch()} />
      ) : null}
      {encounters ? <EncounterList encounters={encounters} /> : null}
    </ClinicalSectionCard>
  );
}

function AllergyWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canManageAllergies(user);
  return (
    <ClinicalSectionCard
      title="Alergias registradas"
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/alergias/nueva`}>Agregar</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      <AllergyList allergies={record.active_allergies} />
    </ClinicalSectionCard>
  );
}

function MedicationWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canManageMedications(user);
  return (
    <ClinicalSectionCard
      title="Medicacion"
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/medicacion/nueva`}>Agregar</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      <MedicationList medications={record.active_medications} />
    </ClinicalSectionCard>
  );
}

function ProblemWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canManageProblems(user);
  return (
    <ClinicalSectionCard
      title="Problemas activos"
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/problemas/nuevo`}>Agregar</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      <ProblemList problems={record.active_problems} />
    </ClinicalSectionCard>
  );
}

function VitalsWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canRecordVitals(user);
  const vitalsQuery = useQuery({
    queryKey: ["vital-signs", patientId],
    queryFn: () => listVitalSigns(patientId),
    enabled: !DEMO_MODE,
  });
  const vitals = DEMO_MODE ? (record.latest_vitals ? [record.latest_vitals] : []) : (vitalsQuery.data ?? []);

  return (
    <div className="space-y-4">
      <VitalsStrip vital={record.latest_vitals} />
      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <ClinicalSectionCard title="Tendencia">
          <LatestVitalsTrend vitals={vitals} />
        </ClinicalSectionCard>
        <ClinicalSectionCard
          title="Nuevo control"
          description="Cada registro se captura en una pantalla dedicada."
          action={
            canWrite ? (
              <Button asChild size="sm">
                <Link href={`/pacientes/${patientId}/signos-vitales/nuevo`}>Registrar</Link>
              </Button>
            ) : (
              <NoPermissionButton label="Sin permiso" />
            )
          }
        >
          <EmptyState title="Accion separada" description="Usa registrar para abrir el formulario de signos." />
        </ClinicalSectionCard>
      </div>
    </div>
  );
}

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

export function NewProblemPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageProblems(user);
  const [formState, setFormState] = useState({
    title: "",
    code_system: "",
    code: "",
    onset_date: "",
    notes: "",
  });
  const mutation = useMutation({
    mutationFn: (payload: ActiveProblemCreate) => createActiveProblem(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
      router.push(`/pacientes/${patientId}/problemas`);
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="problemas">
      <div className="max-w-xl space-y-5">
        <BackLink href={`/pacientes/${patientId}/problemas`} label="Problemas" />
        <PageTitle title="Agregar problema activo" description="Problema clinico longitudinal." />
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite registrar problemas activos." />
        ) : null}
        <ClinicalSectionCard title="Problema">
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

export function NewVitalSignPage() {
  const patientId = usePatientId();
  const router = useRouter();
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
          <ErrorState description="Tu rol actual no permite registrar signos vitales." />
        ) : null}
        <ClinicalSectionCard title="Control">
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

function PatientAiSuggestionsPanel({ patientId, canUseAi }: { patientId: string; canUseAi: boolean }) {
  const suggestionsQuery = useQuery({
    queryKey: ["patient-ai-suggestions", patientId],
    queryFn: () => createPatientAiSuggestions(patientId, { focus: "summary" }),
    enabled: !DEMO_MODE && canUseAi,
    staleTime: 60_000,
  });

  if (DEMO_MODE) {
    return (
      <ClinicalSectionCard title="Sugerencias Ollama" description="Borrador IA - requiere revision humana.">
        <EmptyState title="IA no disponible en demo" description="Usa API real para sugerencias locales." />
      </ClinicalSectionCard>
    );
  }

  if (!canUseAi) {
    return (
      <ClinicalSectionCard title="Sugerencias Ollama" description="Borrador IA - requiere revision humana.">
        <EmptyState
          title="IA no permitida para este rol"
          description="Disponible para medico, admin o dev."
        />
      </ClinicalSectionCard>
    );
  }

  return (
    <ClinicalSectionCard
      title="Sugerencias Ollama"
      description="Borrador IA - requiere revision humana."
      action={
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={suggestionsQuery.isFetching}
          onClick={() => suggestionsQuery.refetch()}
        >
          {suggestionsQuery.isFetching ? "Revisando..." : "Actualizar"}
        </Button>
      }
    >
      {suggestionsQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {suggestionsQuery.isError ? (
        <ErrorState description="No se pudo obtener sugerencias. La ficha sigue operativa." />
      ) : null}
      {suggestionsQuery.data ? <PatientAiSuggestionList response={suggestionsQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function PatientAiSuggestionList({ response }: { response: PatientAiSuggestionsResponse }) {
  return (
    <div className="space-y-3">
      <div className="rounded-md border bg-muted/30 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={response.status === "draft" ? "safe" : "warning"}>{response.status}</Badge>
          <Badge variant="outline">{response.provider}</Badge>
          {response.model ? <Badge variant="outline">{response.model}</Badge> : null}
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{response.summary}</p>
      </div>
      <div className="space-y-2">
        {response.suggestions.map((suggestion) => (
          <div key={`${suggestion.title}-${suggestion.detail}`} className="rounded-md border p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{suggestion.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{suggestion.detail}</p>
              </div>
              <Badge variant={suggestion.severity === "critical" ? "warning" : "outline"}>
                {suggestion.severity}
              </Badge>
            </div>
            {suggestion.action_label ? (
              <p className="mt-2 text-xs text-muted-foreground">{suggestion.action_label}</p>
            ) : null}
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">Borrador IA - requiere revision humana.</p>
    </div>
  );
}

function AuditWorkspace({ patientId }: { patientId: string }) {
  const auditQuery = useQuery({
    queryKey: ["audit-events", patientId],
    queryFn: () => listAuditEvents(patientId),
    enabled: !DEMO_MODE,
  });

  return (
    <ClinicalSectionCard title="Auditoria">
      {DEMO_MODE ? (
        <EmptyState title="Auditoria no disponible en demo" description="Usa la API real para ver eventos." />
      ) : null}
      {auditQuery.isLoading ? <LoadingRows rows={4} /> : null}
      {auditQuery.isError ? (
        <ErrorState description="No se pudo cargar auditoria." onRetry={() => auditQuery.refetch()} />
      ) : null}
      {auditQuery.data ? <AuditTimeline events={auditQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function PatientList({ patients }: { patients: Patient[] }) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {patients.map((patient) => (
        <Link
          key={patient.id}
          href={`/pacientes/${patient.id}/ficha`}
          className="rounded-md border bg-card p-4 transition-colors hover:bg-muted"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">
                {patient.first_name} {patient.last_name}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">{patient.birth_date}</p>
            </div>
            {patient.clinical_identifier ? <Badge variant="outline">{patient.clinical_identifier}</Badge> : null}
          </div>
        </Link>
      ))}
    </div>
  );
}

function PageTitle({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold">{title}</h1>
        {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

function BackLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"
      data-print-hidden="true"
    >
      <ArrowLeft className="h-4 w-4" />
      {label}
    </Link>
  );
}

function NoPermissionButton({ label = "Sin permiso" }: { label?: string }) {
  return (
    <Button type="button" variant="outline" size="sm" disabled>
      {label}
    </Button>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

function SoapTextarea({
  label,
  registration,
}: {
  label: string;
  registration: UseFormRegisterReturn;
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Textarea className="min-h-28" {...registration} />
    </div>
  );
}

function usePatientId() {
  const params = useParams<{ patientId: string }>();
  return params.patientId;
}

function usePatientRecordQuery(patientId: string) {
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const demoRecord = useDemoRecord(patientId);
  return { record: demoRecord ?? recordQuery.data, recordQuery };
}

function useDemoRecord(patientId: string) {
  return useMemo(
    () => (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) ?? demoRecords[0] : null),
    [patientId],
  );
}

function PatientLoadError() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl p-4 md:p-6">
        <ErrorState description="No se pudo cargar el paciente." />
      </div>
    </AppShell>
  );
}

function emptyToNull(value?: string | null) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function numberOrNull(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function toDatetimeLocal(value: Date) {
  const offsetMs = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offsetMs).toISOString().slice(0, 16);
}

const fieldLabels = {
  name: "Nombre",
  dose: "Dosis",
  route: "Via",
  frequency: "Frecuencia",
  systolic_bp: "Sistolica",
  diastolic_bp: "Diastolica",
  heart_rate_bpm: "Frecuencia cardiaca",
  oxygen_saturation_pct: "Saturacion O2",
  temperature_c: "Temperatura C",
};
