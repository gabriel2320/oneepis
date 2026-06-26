"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Activity, Bed, ClipboardList, FileText, Plus, Save, Search, ShieldCheck } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AppShell } from "@/components/layout/app-shell";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientList, PatientQueueMetric } from "@/components/clinical/patient-list-table";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEMO_MODE } from "@/lib/api/client";
import { createPatient, listPatients } from "@/lib/api/patients";
import { demoRecords } from "@/lib/demo-record";
import { canCreatePatient } from "@/lib/permissions";
import type { PatientCreate } from "@/lib/types";
import {
  BackLink,
  Field,
  NoPermissionButton,
  PageTitle,
  emptyToNull,
  patientSchema,
  type PatientFormValues,
} from "./patient-page-shared";

export function PatientsIndexPage() {
  const [search, setSearch] = useState("");
  const { user, isLoading: userLoading } = useCurrentUser();
  const canCreate = canCreatePatient(user);
  const canReadPatients = DEMO_MODE || Boolean(user);
  const isAnonymous = !DEMO_MODE && !userLoading && !user;
  const patientQuery = useQuery({
    queryKey: ["patients", search],
    queryFn: () => listPatients(search),
    enabled: !DEMO_MODE && canReadPatients,
  });
  const patients = DEMO_MODE ? demoRecords.map((item) => item.patient) : canReadPatients ? patientQuery.data : [];
  const patientCount = patients?.length ?? 0;
  const activeCount = patients?.filter((patient) => patient.clinical_status === "active").length ?? 0;
  const hospitalizedCount =
    patients?.filter((patient) => patient.current_care_context === "hospitalized").length ?? 0;
  const ambulatoryCount =
    patients?.filter((patient) => patient.current_care_context === "ambulatory").length ?? 0;

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-5 md:px-6 md:py-7">
        <section className="border-b pb-5">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-md border bg-card px-2.5 py-1 text-xs font-medium text-muted-foreground">
                <ClipboardList className="h-3.5 w-3.5" />
                Mesa de pacientes
              </div>
              <h1 className="mt-3 text-2xl font-semibold tracking-normal md:text-3xl">Pacientes</h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                Busca, abre o crea fichas clinicas desde una entrada sobria. La verdad vive en PostgreSQL,
                con auditoria y permisos por accion.
              </p>
            </div>
            {canCreate ? (
              <Button asChild>
                <Link href="/pacientes/nuevo">
                  <Plus className="h-4 w-4" />
                  Nuevo paciente
                </Link>
              </Button>
            ) : (
              <NoPermissionButton label={userLoading ? "Cargando rol" : "Sin permiso"} />
            )}
          </div>

          <div className="mt-5 grid gap-3 text-sm text-muted-foreground md:grid-cols-3">
            <div className="flex items-center gap-2 rounded-md border bg-card px-3 py-2">
              <FileText className="h-4 w-4 text-primary" />
              Ficha como centro
            </div>
            <div className="flex items-center gap-2 rounded-md border bg-card px-3 py-2">
              <ShieldCheck className="h-4 w-4 text-success" />
              Auditoria por escritura
            </div>
            <div className="flex items-center gap-2 rounded-md border bg-card px-3 py-2">
              <ClipboardList className="h-4 w-4 text-info" />
              Papel clinico gobernado
            </div>
          </div>
        </section>

        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between" data-print-hidden="true">
          <div className="relative w-full max-w-xl">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Buscar por nombre o identificador"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <p className="text-sm text-muted-foreground">
            {isAnonymous
              ? "Sesion requerida"
              : patientQuery.isLoading && !DEMO_MODE
                ? "Cargando fichas..."
                : `${patientCount} fichas visibles`}
          </p>
        </div>

        {!isAnonymous ? (
          <div className="grid gap-3 md:grid-cols-4">
            <PatientQueueMetric label="Fichas visibles" value={patientCount} icon={<ClipboardList className="h-4 w-4" />} />
            <PatientQueueMetric label="Activas" value={activeCount} icon={<Activity className="h-4 w-4" />} />
            <PatientQueueMetric label="Hospitalizadas" value={hospitalizedCount} icon={<Bed className="h-4 w-4" />} />
            <PatientQueueMetric label="Ambulatorias" value={ambulatoryCount} icon={<FileText className="h-4 w-4" />} />
          </div>
        ) : null}

        {patientQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={4} /> : null}
        {patientQuery.isError && !DEMO_MODE ? (
          <ErrorState
            description="Verifica que FastAPI este corriendo y que PostgreSQL este disponible."
            onRetry={() => patientQuery.refetch()}
          />
        ) : null}
        {isAnonymous ? (
          <EmptyState
            title="Inicia sesion para abrir la mesa"
            description="El listado de fichas requiere un usuario local autorizado."
            action={
              <Button asChild>
                <Link href="/login">Ingresar</Link>
              </Button>
            }
          />
        ) : null}
        {!isAnonymous && patients && patients.length === 0 ? (
          <EmptyState
            title="Mesa de pacientes limpia"
            description="Crea la primera ficha de desarrollo o inicia sesion con un rol autorizado para escribir."
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
        {!isAnonymous && patients && patients.length > 0 ? <PatientList patients={patients} /> : null}
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
