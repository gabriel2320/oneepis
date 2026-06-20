"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Plus, Save, Search } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AppShell } from "@/components/layout/app-shell";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DEMO_MODE } from "@/lib/api/client";
import { createPatient, listPatients } from "@/lib/api/patients";
import { demoRecords } from "@/lib/demo-record";
import { canCreatePatient } from "@/lib/permissions";
import type { Patient, PatientCreate } from "@/lib/types";
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

export function PatientList({ patients }: { patients: Patient[] }) {
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
