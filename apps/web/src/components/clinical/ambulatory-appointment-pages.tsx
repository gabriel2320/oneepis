"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarPlus, Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { ModulePage } from "@/components/clinical/module-pages";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { listAppointments, createPatientAppointment } from "@/lib/api/appointments";
import { DEMO_MODE } from "@/lib/api/client";
import { listPatients } from "@/lib/api/patients";
import { demoAppointments, demoRecords } from "@/lib/demo-record";
import { canManageEncounters } from "@/lib/permissions";
import type { ClinicalAppointment, Patient } from "@/lib/types";

import { Field, emptyToNull, toDatetimeLocal } from "./patient-page-shared";

type AppointmentFormState = {
  patient_id: string;
  starts_at: string;
  ends_at: string;
  reason: string;
  location_label: string;
  clinician_label: string;
  notes: string;
};

const statusLabel: Record<ClinicalAppointment["status"], string> = {
  scheduled: "Programada",
  check_in: "Check-in",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  no_show: "No asistio",
};

export function AmbulatoryAppointmentPage() {
  const [selectedDate, setSelectedDate] = useState(DEMO_MODE ? "2026-06-24" : todayDate());
  const { start, end } = dayRange(selectedDate);
  const appointmentsQuery = useQuery({
    queryKey: ["appointments", selectedDate],
    queryFn: () => listAppointments(start, end),
    enabled: !DEMO_MODE,
  });
  const patientsQuery = useQuery({
    queryKey: ["patients", "agenda"],
    queryFn: () => listPatients(),
    enabled: !DEMO_MODE,
  });
  const patients = DEMO_MODE ? demoRecords.map((record) => record.patient) : (patientsQuery.data ?? []);
  const appointments = DEMO_MODE
    ? demoAppointments.filter((appointment) => appointment.starts_at.startsWith(selectedDate))
    : (appointmentsQuery.data ?? []);

  return (
    <ModulePage
      title="Agenda"
      description="Agenda ambulatoria persistida, con estados reales y enlace a atencion."
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
        <ClinicalSectionCard title="Agenda ambulatoria" description="Filtra por dia y conserva trazabilidad.">
          <div className="mb-4 max-w-xs">
            <Field label="Dia de agenda">
              <Input
                type="date"
                value={selectedDate}
                onChange={(event) => setSelectedDate(event.target.value)}
              />
            </Field>
          </div>
          {appointmentsQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
          {appointmentsQuery.isError && !DEMO_MODE ? (
            <ErrorState description="No se pudo cargar la agenda." onRetry={() => appointmentsQuery.refetch()} />
          ) : null}
          {!appointmentsQuery.isLoading && !appointmentsQuery.isError ? (
            <AppointmentList appointments={appointments} patients={patients} />
          ) : null}
        </ClinicalSectionCard>
        <AppointmentCreatePanel
          patients={patients}
          patientsLoading={patientsQuery.isLoading && !DEMO_MODE}
          selectedDate={selectedDate}
        />
      </div>
    </ModulePage>
  );
}

function AppointmentList({
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

function AppointmentCreatePanel({
  patients,
  patientsLoading,
  selectedDate,
}: {
  patients: Patient[];
  patientsLoading: boolean;
  selectedDate: string;
}) {
  const queryClient = useQueryClient();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageEncounters(user);
  const [formState, setFormState] = useState<AppointmentFormState>(() =>
    emptyAppointmentForm(selectedDate),
  );
  const selectedPatientId = formState.patient_id || patients[0]?.id || "";
  const mutation = useMutation({
    mutationFn: (payload: AppointmentFormState) =>
      createPatientAppointment(payload.patient_id, {
        starts_at: new Date(payload.starts_at).toISOString(),
        ends_at: payload.ends_at ? new Date(payload.ends_at).toISOString() : null,
        reason: payload.reason,
        location_label: emptyToNull(payload.location_label),
        clinician_label: emptyToNull(payload.clinician_label),
        notes: emptyToNull(payload.notes),
      }),
    onSuccess: async () => {
      setFormState(emptyAppointmentForm(selectedDate));
      await queryClient.invalidateQueries({ queryKey: ["appointments", selectedDate] });
    },
  });
  const disabled =
    mutation.isPending || DEMO_MODE || !canWrite || patients.length === 0 || patientsLoading;

  return (
    <ClinicalSectionCard
      title="Nueva cita"
      description="Crea una cita programada; la atencion clinica sigue ocurriendo en el encuentro."
    >
      {DEMO_MODE ? <ErrorState description="El modo demo no permite guardar citas reales." /> : null}
      {!DEMO_MODE && !userLoading && !canWrite ? (
        <ErrorState description="Tu rol actual no permite crear citas ambulatorias." />
      ) : null}
      {patients.length === 0 && !patientsLoading ? (
        <EmptyState title="Sin pacientes disponibles" description="Crea un paciente antes de agendar." />
      ) : null}
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate({ ...formState, patient_id: selectedPatientId });
        }}
      >
        <Field label="Paciente">
          <select
            aria-label="Paciente de la cita"
            className="h-9 w-full rounded-md border bg-background px-3 text-sm"
            disabled={disabled}
            value={selectedPatientId}
            onChange={(event) => setFormState({ ...formState, patient_id: event.target.value })}
          >
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.first_name} {patient.last_name}
              </option>
            ))}
          </select>
        </Field>
        <AppointmentInput
          label="Inicio"
          type="datetime-local"
          value={formState.starts_at}
          disabled={disabled}
          onChange={(value) => setFormState({ ...formState, starts_at: value })}
        />
        <AppointmentInput
          label="Termino"
          type="datetime-local"
          value={formState.ends_at}
          disabled={disabled}
          onChange={(value) => setFormState({ ...formState, ends_at: value })}
        />
        <AppointmentInput
          label="Motivo"
          value={formState.reason}
          disabled={disabled}
          onChange={(value) => setFormState({ ...formState, reason: value })}
        />
        <AppointmentInput
          label="Ubicacion"
          value={formState.location_label}
          disabled={disabled}
          onChange={(value) => setFormState({ ...formState, location_label: value })}
        />
        <AppointmentInput
          label="Profesional/equipo"
          value={formState.clinician_label}
          disabled={disabled}
          onChange={(value) => setFormState({ ...formState, clinician_label: value })}
        />
        <Field label="Notas">
          <Textarea
            disabled={disabled}
            value={formState.notes}
            onChange={(event) => setFormState({ ...formState, notes: event.target.value })}
          />
        </Field>
        <Button type="submit" disabled={disabled || !selectedPatientId || !formState.reason.trim()}>
          {mutation.isPending ? <CalendarPlus className="h-4 w-4" /> : <Save className="h-4 w-4" />}
          {mutation.isPending ? "Guardando..." : "Guardar cita"}
        </Button>
      </form>
      {mutation.isError ? <p className="mt-3 text-sm text-destructive">No se pudo guardar la cita.</p> : null}
    </ClinicalSectionCard>
  );
}

function AppointmentInput({
  label,
  value,
  disabled,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <Field label={label}>
      <Input
        type={type}
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </Field>
  );
}

function emptyAppointmentForm(selectedDate: string): AppointmentFormState {
  const start = new Date(`${selectedDate}T09:00:00`);
  const end = new Date(`${selectedDate}T09:30:00`);
  return {
    patient_id: "",
    starts_at: toDatetimeLocal(start),
    ends_at: toDatetimeLocal(end),
    reason: "",
    location_label: "",
    clinician_label: "",
    notes: "",
  };
}

function todayDate() {
  return new Date().toISOString().slice(0, 10);
}

function dayRange(date: string) {
  return {
    start: new Date(`${date}T00:00:00`).toISOString(),
    end: new Date(`${date}T23:59:59`).toISOString(),
  };
}

function patientNameMap(patients: Patient[]) {
  return new Map(patients.map((patient) => [patient.id, `${patient.first_name} ${patient.last_name}`]));
}
