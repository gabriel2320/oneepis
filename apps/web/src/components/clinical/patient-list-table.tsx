import Link from "next/link";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import type { Patient } from "@/lib/types";

export function PatientList({ patients }: { patients: Patient[] }) {
  return (
    <div className="overflow-hidden rounded-md border bg-card" aria-label="Mesa de pacientes">
      <div className="hidden grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto] gap-4 border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground md:grid">
        <span>Paciente</span>
        <span>Contexto</span>
        <span className="text-right">Estado</span>
      </div>
      {patients.map((patient) => (
        <Link
          key={patient.id}
          href={`/pacientes/${patient.id}/ficha`}
          className="grid gap-3 border-b p-4 transition-colors last:border-b-0 hover:bg-muted/70 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto] md:items-center"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">
              {patient.first_name} {patient.last_name}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {patient.clinical_identifier ? `ID ${patient.clinical_identifier}` : "Sin identificador clinico"} -{" "}
              nacimiento {patient.birth_date}
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            <p>{careContextLabel(patient.current_care_context)}</p>
            <p className="mt-1 text-xs">Actualizada {formatDate(patient.updated_at)}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 md:justify-end">
            <Badge variant={patient.clinical_status === "active" ? "safe" : "outline"}>
              {clinicalStatusLabel(patient.clinical_status)}
            </Badge>
            {patient.current_care_context !== "unknown" ? (
              <Badge variant="secondary">{careContextLabel(patient.current_care_context)}</Badge>
            ) : null}
          </div>
        </Link>
      ))}
    </div>
  );
}

export function PatientQueueMetric({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: ReactNode;
}) {
  return (
    <div className="rounded-md border bg-card p-3">
      <div className="flex items-center justify-between gap-3 text-muted-foreground">
        <p className="text-xs font-medium">{label}</p>
        {icon}
      </div>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function clinicalStatusLabel(status: Patient["clinical_status"]) {
  const labels: Record<Patient["clinical_status"], string> = {
    active: "Activa",
    archived: "Archivada",
    closed: "Cerrada",
    draft: "Borrador",
  };
  return labels[status];
}

function careContextLabel(context: Patient["current_care_context"]) {
  const labels: Record<Patient["current_care_context"], string> = {
    ambulatory: "Ambulatoria",
    hospitalized: "Hospitalizada",
    unknown: "Sin contexto",
  };
  return labels[context];
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-CL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
