"use client";

import Link from "next/link";
import { useMemo } from "react";

import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClinicalAppointment, Patient } from "@/lib/types";

const statusLabel: Record<ClinicalAppointment["status"], string> = {
  scheduled: "Programada",
  check_in: "Check-in",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  no_show: "No asistio",
};

export function AppointmentList({
  appointments,
  patients,
}: {
  appointments: ClinicalAppointment[];
  patients: Patient[];
}) {
  const patientNames = useMemo(() => patientNameMap(patients), [patients]);
  if (appointments.length === 0) {
    return (
      <EmptyState
        title="Sin citas para este dia"
        description="La agenda real queda vacia hasta crear una cita persistida."
      />
    );
  }

  return (
    <div className="space-y-3">
      {appointments.map((appointment) => (
        <article key={appointment.id} className="rounded-md border p-3">
          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-sm font-semibold">
                {patientNames.get(appointment.patient_id) ?? "Paciente sin nombre"}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{appointment.reason}</p>
            </div>
            <Badge variant={appointment.status === "cancelled" ? "outline" : "safe"}>
              {statusLabel[appointment.status]}
            </Badge>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {formatDateTime(appointment.starts_at)}
            {appointment.ends_at ? ` - ${formatDateTime(appointment.ends_at)}` : ""}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {appointment.location_label || "Ubicacion pendiente"} -{" "}
            {appointment.clinician_label || "Profesional/equipo pendiente"}
          </p>
          {appointment.notes ? <p className="mt-2 text-sm">{appointment.notes}</p> : null}
          <Button asChild className="mt-3" variant="outline" size="sm">
            <Link href={`/consulta/pacientes/${appointment.patient_id}/atencion`}>
              Abrir atencion
            </Link>
          </Button>
        </article>
      ))}
    </div>
  );
}

function patientNameMap(patients: Patient[]) {
  return new Map(patients.map((patient) => [patient.id, `${patient.first_name} ${patient.last_name}`]));
}
