"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import type { UseFormRegisterReturn } from "react-hook-form";
import { z } from "zod";
import { ArrowLeft } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DEMO_MODE } from "@/lib/api/client";
import { getPatientRecord } from "@/lib/api/patients";
import { demoRecords } from "@/lib/demo-record";
import type { CareContext, EncounterStatus, EncounterType, PatientClinicalStatus } from "@/lib/types";

export const patientSchema = z.object({
  first_name: z.string().min(1, "Nombre requerido"),
  last_name: z.string().min(1, "Apellido requerido"),
  preferred_name: z.string().optional(),
  birth_date: z.string().min(1, "Fecha requerida"),
  sex_at_birth: z.enum(["female", "male", "intersex", "unknown"]),
  clinical_identifier: z.string().optional(),
  contact_phone: z.string().optional(),
  email: z.string().email("Email invalido").optional().or(z.literal("")),
});

export type PatientFormValues = z.infer<typeof patientSchema>;

export const soapSchema = z.object({
  encounter_id: z.string().optional(),
  title: z.string().min(1, "Titulo requerido"),
  occurred_at: z.string().min(1, "Fecha requerida"),
  subjective: z.string().optional(),
  objective: z.string().optional(),
  assessment: z.string().optional(),
  plan: z.string().optional(),
});

export type SoapFormValues = z.infer<typeof soapSchema>;

export const encounterTypeOptions: { value: EncounterType; label: string }[] = [
  { value: "ambulatory", label: "Ambulatorio" },
  { value: "hospitalization", label: "Hospitalizacion" },
  { value: "emergency", label: "Urgencia" },
  { value: "unknown", label: "No definido" },
];

export const encounterStatusOptions: { value: EncounterStatus; label: string }[] = [
  { value: "scheduled", label: "Programado" },
  { value: "in_progress", label: "En curso" },
  { value: "completed", label: "Completado" },
  { value: "cancelled", label: "Cancelado" },
];

export const clinicalStatusOptions: { value: PatientClinicalStatus; label: string }[] = [
  { value: "draft", label: "Borrador" },
  { value: "active", label: "Activa" },
  { value: "closed", label: "Cerrada" },
  { value: "archived", label: "Archivada" },
];

export const careContextOptions: { value: CareContext; label: string }[] = [
  { value: "unknown", label: "No definido" },
  { value: "ambulatory", label: "Ambulatorio" },
  { value: "hospitalized", label: "Hospitalizado" },
];

export type PatientSection =
  | "ficha"
  | "encuentros"
  | "eventos"
  | "ai-chart"
  | "evoluciones"
  | "problemas"
  | "alergias"
  | "medicacion"
  | "signos-vitales"
  | "documentos"
  | "ia"
  | "auditoria";

export function PageTitle({
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

export function BackLink({ href, label }: { href: string; label: string }) {
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

export function NoPermissionButton({ label = "Sin permiso" }: { label?: string }) {
  return (
    <Button type="button" variant="outline" size="sm" disabled>
      {label}
    </Button>
  );
}

export function Field({
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

export function SoapTextarea({
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

export function usePatientId() {
  const params = useParams<{ patientId: string }>();
  return params.patientId;
}

export function usePatientRecordQuery(patientId: string) {
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
    () => (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) : null),
    [patientId],
  );
}

export function PatientLoadError() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl p-4 md:p-6">
        <ErrorState description="No se pudo cargar el paciente." />
      </div>
    </AppShell>
  );
}

export function emptyToNull(value?: string | null) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export function numberOrNull(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function toDatetimeLocal(value: Date) {
  const offsetMs = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offsetMs).toISOString().slice(0, 16);
}

export const fieldLabels = {
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
