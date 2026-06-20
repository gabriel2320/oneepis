"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm, type UseFormRegisterReturn } from "react-hook-form";
import { z } from "zod";
import { ArrowLeft, Plus, Save, Search } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { AiInsightPanel } from "@/components/clinical-record/ai-insight-panel";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import {
  AiSafetyPanel,
  AllergyList,
  AuditTimeline,
  ClinicalTimeline,
  CriticalAlerts,
  LatestVitalsTrend,
  MedicationList,
  PatientLongitudinalSummary,
  PrintActions,
  ProblemList,
  QuickSoapEditor,
  VitalsStrip,
} from "@/components/clinical/widgets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createAllergy, createClinicalEntry, createMedication, createVitalSign, listAuditEvents, listVitalSigns } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { createPatient, getPatientRecord, listPatients } from "@/lib/api/patients";
import { demoRecords } from "@/lib/demo-record";
import type {
  AllergyCreate,
  MedicationCreate,
  Patient,
  PatientCreate,
  PatientRecordSnapshot,
  VitalSignCreate,
} from "@/lib/types";
import { cn } from "@/lib/utils";
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

const patientSections = [
  { key: "ficha", label: "Ficha" },
  { key: "evoluciones", label: "Evoluciones" },
  { key: "problemas", label: "Problemas" },
  { key: "alergias", label: "Alergias" },
  { key: "medicacion", label: "Medicacion" },
  { key: "signos-vitales", label: "Signos vitales" },
  { key: "documentos", label: "Documentos" },
  { key: "ia", label: "IA" },
  { key: "auditoria", label: "Auditoria" },
] as const;

type PatientSection = (typeof patientSections)[number]["key"];

export function PatientsIndexPage() {
  const [search, setSearch] = useState("");
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
            <Button asChild>
              <Link href="/pacientes/nuevo">
                <Plus className="h-4 w-4" />
                Nuevo
              </Link>
            </Button>
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
              <Button asChild>
                <Link href="/pacientes/nuevo">Crear paciente</Link>
              </Button>
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
              <Button type="submit" disabled={createMutation.isPending || DEMO_MODE}>
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
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const record = useDemoRecord(patientId) ?? recordQuery.data;

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-5 p-4 md:p-6">
        {recordQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
        {recordQuery.isError && !DEMO_MODE ? (
          <ErrorState
            description="No se pudo cargar la ficha del paciente."
            onRetry={() => recordQuery.refetch()}
          />
        ) : null}
        {record ? (
          <>
            <PatientRecordHeader record={record} section={section} />
            <PatientSectionContent record={record} section={section} patientId={patientId} />
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

export function NewSoapEntryPage() {
  const patientId = usePatientId();
  const router = useRouter();
  const queryClient = useQueryClient();
  const record = useDemoRecord(patientId);
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

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-5 p-4 md:p-6">
        <BackLink href={`/pacientes/${patientId}/evoluciones`} label="Evoluciones" />
        <PageTitle
          title="Nueva evolucion SOAP"
          description={record ? `${record.patient.first_name} ${record.patient.last_name}` : "Paciente"}
        />
        {DEMO_MODE ? (
          <ErrorState description="El modo demo no permite guardar evoluciones reales." />
        ) : null}
        <ClinicalSectionCard title="SOAP">
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
            <Button type="submit" disabled={mutation.isPending || DEMO_MODE}>
              <Save className="h-4 w-4" />
              {mutation.isPending ? "Guardando..." : "Guardar borrador"}
            </Button>
            {mutation.isError ? <p className="text-sm text-destructive">No se pudo guardar.</p> : null}
          </form>
        </ClinicalSectionCard>
      </div>
    </AppShell>
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
  if (section === "ficha") {
    return (
      <div className="space-y-4">
        <CriticalAlerts record={record} />
        <VitalsStrip vital={record.latest_vitals} />
        <PatientLongitudinalSummary record={record} />
        <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
          <ClinicalSectionCard
            title="Linea clinica"
            action={<QuickSoapEditor href={`/pacientes/${patientId}/evoluciones/nueva`} />}
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
          </div>
        </div>
      </div>
    );
  }

  if (section === "evoluciones") {
    return (
      <ClinicalSectionCard
        title="Evoluciones"
        action={<QuickSoapEditor href={`/pacientes/${patientId}/evoluciones/nueva`} />}
      >
        <ClinicalTimeline entries={record.recent_entries} />
      </ClinicalSectionCard>
    );
  }

  if (section === "alergias") {
    return <AllergyWorkspace patientId={patientId} record={record} />;
  }

  if (section === "medicacion") {
    return <MedicationWorkspace patientId={patientId} record={record} />;
  }

  if (section === "signos-vitales") {
    return <VitalsWorkspace patientId={patientId} record={record} />;
  }

  if (section === "ia") {
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
    return (
      <ClinicalSectionCard title="Problemas">
        <ProblemList />
      </ClinicalSectionCard>
    );
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

function AllergyWorkspace({ patientId, record }: { patientId: string; record: PatientRecordSnapshot }) {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState({ substance: "", reaction: "", severity: "unknown" });
  const mutation = useMutation({
    mutationFn: (payload: AllergyCreate) => createAllergy(patientId, payload),
    onSuccess: async () => {
      setFormState({ substance: "", reaction: "", severity: "unknown" });
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
    },
  });

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
      <ClinicalSectionCard title="Alergias registradas">
        <AllergyList allergies={record.active_allergies} />
      </ClinicalSectionCard>
      <ClinicalSectionCard title="Agregar alergia">
        <form
          className="space-y-3"
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
          <Input
            placeholder="Sustancia"
            value={formState.substance}
            onChange={(event) => setFormState({ ...formState, substance: event.target.value })}
          />
          <Input
            placeholder="Reaccion"
            value={formState.reaction}
            onChange={(event) => setFormState({ ...formState, reaction: event.target.value })}
          />
          <select
            className="h-9 w-full rounded-md border bg-background px-3 text-sm"
            value={formState.severity}
            onChange={(event) => setFormState({ ...formState, severity: event.target.value })}
          >
            <option value="unknown">Severidad desconocida</option>
            <option value="mild">Leve</option>
            <option value="moderate">Moderada</option>
            <option value="severe">Severa</option>
          </select>
          <Button type="submit" disabled={mutation.isPending || !formState.substance.trim() || DEMO_MODE}>
            {mutation.isPending ? "Guardando..." : "Guardar alergia"}
          </Button>
        </form>
      </ClinicalSectionCard>
    </div>
  );
}

function MedicationWorkspace({ patientId, record }: { patientId: string; record: PatientRecordSnapshot }) {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState({ name: "", dose: "", route: "", frequency: "" });
  const mutation = useMutation({
    mutationFn: (payload: MedicationCreate) => createMedication(patientId, payload),
    onSuccess: async () => {
      setFormState({ name: "", dose: "", route: "", frequency: "" });
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
    },
  });

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
      <ClinicalSectionCard title="Medicacion">
        <MedicationList medications={record.active_medications} />
      </ClinicalSectionCard>
      <ClinicalSectionCard title="Agregar medicamento">
        <form
          className="space-y-3"
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
            <Input
              key={field}
              placeholder={fieldLabels[field]}
              value={formState[field]}
              onChange={(event) => setFormState({ ...formState, [field]: event.target.value })}
            />
          ))}
          <Button type="submit" disabled={mutation.isPending || !formState.name.trim() || DEMO_MODE}>
            {mutation.isPending ? "Guardando..." : "Guardar medicamento"}
          </Button>
        </form>
      </ClinicalSectionCard>
    </div>
  );
}

function VitalsWorkspace({ patientId, record }: { patientId: string; record: PatientRecordSnapshot }) {
  const queryClient = useQueryClient();
  const vitalsQuery = useQuery({
    queryKey: ["vital-signs", patientId],
    queryFn: () => listVitalSigns(patientId),
    enabled: !DEMO_MODE,
  });
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
      setFormState({
        systolic_bp: "",
        diastolic_bp: "",
        heart_rate_bpm: "",
        oxygen_saturation_pct: "",
        temperature_c: "",
      });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["vital-signs", patientId] }),
      ]);
    },
  });
  const vitals = DEMO_MODE ? (record.latest_vitals ? [record.latest_vitals] : []) : (vitalsQuery.data ?? []);

  return (
    <div className="space-y-4">
      <VitalsStrip vital={record.latest_vitals} />
      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <ClinicalSectionCard title="Tendencia">
          <LatestVitalsTrend vitals={vitals} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Nuevo control">
          <form
            className="grid gap-3"
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
                <Input
                  key={field}
                  inputMode="decimal"
                  placeholder={fieldLabels[field]}
                  value={formState[field]}
                  onChange={(event) => setFormState({ ...formState, [field]: event.target.value })}
                />
              ),
            )}
            <Button type="submit" disabled={mutation.isPending || DEMO_MODE}>
              {mutation.isPending ? "Guardando..." : "Guardar signos"}
            </Button>
          </form>
        </ClinicalSectionCard>
      </div>
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

function PatientRecordHeader({
  record,
  section,
}: {
  record: PatientRecordSnapshot;
  section: PatientSection;
}) {
  const patient = record.patient;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 rounded-md border bg-card p-4 md:flex-row md:items-start md:justify-between">
        <div>
          <BackLink href="/pacientes" label="Pacientes" />
          <h1 className="mt-3 text-2xl font-semibold">
            {patient.first_name} {patient.last_name}
          </h1>
          <div className="mt-2 flex flex-wrap gap-2 text-sm text-muted-foreground">
            <span>{patient.birth_date}</span>
            <span>{patient.sex_at_birth}</span>
            {patient.clinical_identifier ? <Badge variant="outline">{patient.clinical_identifier}</Badge> : null}
          </div>
        </div>
        <PrintActions patientId={patient.id} />
      </div>
      <nav className="flex gap-2 overflow-x-auto pb-1" data-print-hidden="true">
        {patientSections.map((item) => (
          <Link
            key={item.key}
            href={`/pacientes/${patient.id}/${item.key}`}
            className={cn(
              "rounded-md border px-3 py-1.5 text-sm font-medium text-muted-foreground",
              section === item.key && "border-primary bg-accent text-accent-foreground",
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
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

function useDemoRecord(patientId: string) {
  return useMemo(
    () => (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) ?? demoRecords[0] : null),
    [patientId],
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
