"use client";

import Link from "next/link";
import { CalendarClock, FileText, Printer, ShieldCheck, UserRound } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PatientRecordSnapshot } from "@/lib/types";

import { formatDateTime } from "./date-format";

export function PatientFormalCover({
  record,
  patientId,
  canEditPatient,
}: {
  record: PatientRecordSnapshot;
  patientId: string;
  canEditPatient: boolean;
}) {
  const patient = record.patient;
  const activeEncounter = record.active_encounter;
  const latestEntry = record.recent_entries[0];
  const severeAllergies = record.active_allergies.filter((allergy) => allergy.severity === "severe");

  return (
    <section className="rounded-md border bg-card p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
            <UserRound className="h-4 w-4 text-primary" />
            Caratula clinica formal
          </p>
          <h2 className="mt-1 text-lg font-semibold">
            {patient.first_name} {patient.last_name}
          </h2>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant={patient.clinical_status === "active" ? "safe" : "outline"}>
              {patient.clinical_status}
            </Badge>
            <Badge variant="outline">{patient.current_care_context}</Badge>
            <Badge variant="outline">{patient.sex_at_birth}</Badge>
            {patient.clinical_identifier ? <Badge variant="outline">{patient.clinical_identifier}</Badge> : null}
            {severeAllergies.length > 0 ? <Badge variant="warning">Alergia critica</Badge> : null}
          </div>
        </div>
        <div className="flex flex-wrap gap-2" data-print-hidden="true">
          {canEditPatient ? (
            <Button asChild variant="outline" size="sm">
              <Link href={`/pacientes/${patientId}/estado`}>Editar estado</Link>
            </Button>
          ) : (
            <Button variant="outline" size="sm" disabled>
              Estado bloqueado
            </Button>
          )}
          <Button asChild variant="outline" size="sm">
            <Link href={`/print/pacientes/${patientId}/ficha`}>
              <Printer className="h-4 w-4" />
              Papel
            </Link>
          </Button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <CoverField label="Nacimiento" value={patient.birth_date} detail="Fuente: patients.birth_date" />
        <CoverField
          label="Contacto"
          value={patient.contact_phone || patient.email || "No registrado"}
          detail="Fuente: PatientRead"
        />
        <CoverField
          label="Problemas activos"
          value={`${record.active_problems.length}`}
          detail="Fuente: active_problems"
        />
        <CoverField
          label="Medicacion activa"
          value={`${record.active_medications.length}`}
          detail="Fuente: medications"
        />
        <CoverField
          label="Alergias activas"
          value={`${record.active_allergies.length}`}
          detail="Fuente: allergies"
        />
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <TracePanel
          icon={<CalendarClock className="h-4 w-4 text-primary" />}
          title="Episodio actual"
          value={
            activeEncounter
              ? `${activeEncounter.reason} (${activeEncounter.type})`
              : "Sin encuentro activo"
          }
          detail={
            activeEncounter
              ? `Inicio ${formatDateTime(activeEncounter.started_at)} - ID ${activeEncounter.id}`
              : "La ficha sigue como resumen longitudinal hasta abrir encuentro."
          }
        />
        <TracePanel
          icon={<FileText className="h-4 w-4 text-primary" />}
          title="Ultimo acto clinico"
          value={latestEntry ? latestEntry.title : "Sin evoluciones"}
          detail={
            latestEntry
              ? `${formatDateTime(latestEntry.occurred_at)} - ${latestEntry.status} - ID ${latestEntry.id}`
              : "Crear SOAP cuando exista acto clinico documentable."
          }
        />
        <TracePanel
          icon={<ShieldCheck className="h-4 w-4 text-primary" />}
          title="Estado documental"
          value="Documento de desarrollo"
          detail="No equivale a firma clinica legal, receta valida ni orden ejecutable."
        />
      </div>
    </section>
  );
}

function CoverField({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border bg-background p-3">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}

function TracePanel({
  icon,
  title,
  value,
  detail,
}: {
  icon: ReactNode;
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border bg-background p-3">
      <p className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        {icon}
        {title}
      </p>
      <p className="mt-2 text-sm font-semibold">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}
