"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CalendarPlus, Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState, ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createPatientAppointment } from "@/lib/api/appointments";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageEncounters } from "@/lib/permissions";
import type { Patient } from "@/lib/types";

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

export function AppointmentCreatePanel({
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
