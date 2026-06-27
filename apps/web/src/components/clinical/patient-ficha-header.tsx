"use client";

import type { ReactNode } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { careContextLabel, clinicalStatusLabel } from "@/lib/patient-display";
import type { PatientRecordSnapshot } from "@/lib/types";

import { formatDateTime } from "./date-format";
import { NoPermissionButton } from "./patient-page-shared";

export function PatientFichaHeader({
  patientId,
  record,
  canEditPatient,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  canEditPatient: boolean;
}) {
  const patient = record.patient;
  const fullName = [patient.first_name, patient.last_name].filter(Boolean).join(" ");
  const severeAllergies = record.active_allergies.filter((item) => item.severity === "severe");
  const lastEntry = record.recent_entries[0] ?? null;

  return (
    <div className="rounded-md border bg-card p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0 space-y-1">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Hoja clinica viva</p>
          <p className="text-lg font-semibold text-foreground">{fullName}</p>
          <p className="text-xs text-muted-foreground">
            {patient.clinical_identifier ?? "Sin identificador"} · {sexLabel(patient.sex_at_birth)} ·
            Nacimiento {patient.birth_date}
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Badge variant="outline">{clinicalStatusLabel(patient.clinical_status)}</Badge>
            <Badge variant="outline">{careContextLabel(patient.current_care_context)}</Badge>
            {severeAllergies.length > 0 ? (
              <Badge variant="warning">
                Alergias criticas: {severeAllergies.map((item) => item.substance).join(", ")}
              </Badge>
            ) : (
              <Badge variant="outline">Sin alergias criticas</Badge>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2" data-print-hidden="true">
          {canEditPatient ? (
            <Button asChild variant="outline" size="sm">
              <Link href={`/pacientes/${patientId}/estado`}>Editar estado</Link>
            </Button>
          ) : (
            <NoPermissionButton label="Estado bloqueado" />
          )}
          <Button asChild variant="outline" size="sm">
            <Link href={`/print/pacientes/${patientId}/ficha`}>Ver papel</Link>
          </Button>
        </div>
      </div>
      <dl className="mt-3 grid gap-3 border-t pt-3 sm:grid-cols-3">
        <HeaderFact label="Problemas activos">
          {record.active_problems.length === 0
            ? "Sin antecedentes activos"
            : record.active_problems.map((item) => item.title).join(", ")}
        </HeaderFact>
        <HeaderFact label="Medicacion vigente">
          {record.active_medications.length === 0
            ? "Sin medicacion activa"
            : record.active_medications.map((item) => item.name).join(", ")}
        </HeaderFact>
        <HeaderFact label="Ultima atencion">
          {lastEntry ? `${lastEntry.title} · ${formatDateTime(lastEntry.occurred_at)}` : "Sin registros"}
        </HeaderFact>
      </dl>
    </div>
  );
}

function HeaderFact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-sm text-foreground">{children}</dd>
    </div>
  );
}

function sexLabel(sex: string) {
  const labels: Record<string, string> = {
    male: "Masculino",
    female: "Femenino",
    intersex: "Intersexual",
    unknown: "Sexo sin dato",
  };
  return labels[sex] ?? "Sexo sin dato";
}
