"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CalendarClock } from "lucide-react";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { AmbulatoryClinicalShell } from "@/components/clinical/clinical-domain-shell";
import { formatDateTime } from "@/components/clinical/date-format";
import { HistoricalDiagnosisContextCard } from "@/components/clinical/historical-diagnosis-context";
import { PatientClinicalLoading } from "@/components/clinical/patient-clinical-shell";
import {
  AllergyList,
  ClinicalTimeline,
  CriticalAlerts,
  EncounterList,
  MedicationList,
  PatientLongitudinalSummary,
  ProblemList,
  VitalsStrip,
} from "@/components/clinical/patient-widgets";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { listPatientAppointments } from "@/lib/api/appointments";
import { ambulatoryEncounters, ambulatoryEntries } from "@/lib/ambulatory-workflows";
import { DEMO_MODE } from "@/lib/api/client";
import { listClinicalEncounters } from "@/lib/api/clinical-record";
import { demoAppointments, demoEncounters } from "@/lib/demo-record";
import type { ClinicalAppointment, PatientRecordSnapshot } from "@/lib/types";

import {
  BackLink,
  PageTitle,
  PatientLoadError,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function AmbulatorySummaryPage() {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <AmbulatoryClinicalShell record={record} activeSection="resumen-ambulatorio">
      <div className="space-y-5">
        <BackLink href="/consulta" label="Consulta" />
        <PageTitle
          title="Resumen ambulatorio"
          description="Lectura de apoyo para la atencion clinica ambulatoria; no crea recetas ni ordenes."
          action={
            <Button asChild variant="outline" size="sm">
              <Link href={`/consulta/pacientes/${patientId}/atencion`}>Abrir atencion</Link>
            </Button>
          }
        />
        <AmbulatorySummaryWorkspace patientId={patientId} record={record} />
      </div>
    </AmbulatoryClinicalShell>
  );
}

function AmbulatorySummaryWorkspace({
  patientId,
  record,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
}) {
  const encountersQuery = useQuery({
    queryKey: ["clinical-encounters", patientId],
    queryFn: () => listClinicalEncounters(patientId),
    enabled: !DEMO_MODE,
  });
  const appointmentsQuery = useQuery({
    queryKey: ["patient-appointments", patientId],
    queryFn: () => listPatientAppointments(patientId),
    enabled: !DEMO_MODE,
  });
  const encounters = DEMO_MODE
    ? demoEncounters.filter((encounter) => encounter.patient_id === patientId)
    : (encountersQuery.data ?? []);
  const appointments = DEMO_MODE
    ? demoAppointments.filter((appointment) => appointment.patient_id === patientId)
    : (appointmentsQuery.data ?? []);
  const ambulatoryEncounterItems = ambulatoryEncounters(encounters);
  const ambulatoryEntryItems = ambulatoryEntries(record.recent_entries, ambulatoryEncounterItems);

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
      <div className="space-y-5">
        <CriticalAlerts record={record} />
        <ClinicalSectionCard title="Snapshot ambulatorio">
          <div className="space-y-4">
            <PatientLongitudinalSummary record={record} />
            <VitalsStrip vital={record.latest_vitals} />
          </div>
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Antecedentes y tratamientos">
          <div className="grid gap-4 lg:grid-cols-3">
            <ProblemList problems={record.active_problems} />
            <AllergyList allergies={record.active_allergies} />
            <MedicationList medications={record.active_medications} />
          </div>
        </ClinicalSectionCard>
        <HistoricalDiagnosisContextCard
          diagnoses={record.historical_diagnoses}
          title="Contexto historico ambulatorio"
        />
        <ClinicalSectionCard title="Evoluciones ambulatorias recientes">
          <ClinicalTimeline entries={ambulatoryEntryItems} />
        </ClinicalSectionCard>
      </div>
      <div className="space-y-5">
        <ClinicalSectionCard title="Citas del paciente" description="Agenda minima persistida.">
          {appointmentsQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
          {appointmentsQuery.isError && !DEMO_MODE ? (
            <ErrorState description="No se pudieron cargar las citas del paciente." />
          ) : null}
          {!appointmentsQuery.isLoading || DEMO_MODE ? (
            <AppointmentSummaryList appointments={appointments} />
          ) : null}
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Atenciones ambulatorias">
          {encountersQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
          {encountersQuery.isError && !DEMO_MODE ? (
            <ErrorState description="No se pudieron cargar las atenciones ambulatorias." />
          ) : null}
          {!encountersQuery.isLoading || DEMO_MODE ? (
            <EncounterList encounters={ambulatoryEncounterItems} />
          ) : null}
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Limites declarados">
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>No emite receta valida, firma clinica, folio ni orden ejecutable.</li>
            <li>Admision/preconsulta, seguimiento formal e interconsultas siguen futuros.</li>
            <li>La ficha longitudinal sigue siendo la fuente completa del paciente.</li>
          </ul>
        </ClinicalSectionCard>
      </div>
    </div>
  );
}

function AppointmentSummaryList({ appointments }: { appointments: ClinicalAppointment[] }) {
  if (appointments.length === 0) {
    return <EmptyState title="Sin citas" description="No hay citas ambulatorias registradas." />;
  }

  return (
    <div className="space-y-2">
      {sortAppointments(appointments).map((appointment) => (
        <div key={appointment.id} className="rounded-md border p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="flex items-center gap-2 text-sm font-semibold">
                <CalendarClock className="h-4 w-4 text-primary" />
                {appointment.reason}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {formatDateTime(appointment.starts_at)}
                {appointment.location_label ? ` - ${appointment.location_label}` : ""}
              </p>
              {appointment.clinician_label ? (
                <p className="mt-1 text-xs text-muted-foreground">{appointment.clinician_label}</p>
              ) : null}
            </div>
            <Badge variant={appointment.status === "cancelled" ? "outline" : "safe"}>
              {appointmentStatusLabel(appointment.status)}
            </Badge>
          </div>
        </div>
      ))}
    </div>
  );
}

function sortAppointments(appointments: ClinicalAppointment[]) {
  return appointments
    .slice()
    .sort((left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime());
}

function appointmentStatusLabel(status: ClinicalAppointment["status"]) {
  const labels: Record<ClinicalAppointment["status"], string> = {
    scheduled: "Programada",
    check_in: "Check-in",
    in_progress: "En curso",
    completed: "Completada",
    cancelled: "Cancelada",
    no_show: "No show",
  };
  return labels[status];
}
