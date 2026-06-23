"use client";

import { ClipboardCheck, Save } from "lucide-react";

import { formatDateTime } from "@/components/clinical/date-format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AppointmentStatus, ClinicalAppointment } from "@/lib/types";

import { Field, toDatetimeLocal } from "./patient-page-shared";

export type PreconsultPriority = "routine" | "priority" | "urgent" | "unknown";

export type PreconsultFormState = {
  appointment_id: string;
  occurred_at: string;
  identity_checked: boolean;
  chief_complaint: string;
  triage_priority: PreconsultPriority;
  allergies_reviewed: boolean;
  medications_reviewed: boolean;
  missing_data: string;
  human_action: string;
  temperature_c: string;
  systolic_bp: string;
  diastolic_bp: string;
  heart_rate_bpm: string;
  respiratory_rate_bpm: string;
  oxygen_saturation_pct: string;
};

const priorityLabels: Record<PreconsultPriority, string> = {
  routine: "Rutina",
  priority: "Prioritaria",
  urgent: "Urgente",
  unknown: "No definida",
};

const statusLabels: Record<AppointmentStatus, string> = {
  scheduled: "Programada",
  check_in: "Check-in",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  no_show: "No asistio",
};

export function PreconsultForm({
  appointments,
  disabled,
  formState,
  setFormState,
  onSubmit,
}: {
  appointments: ClinicalAppointment[];
  disabled: boolean;
  formState: PreconsultFormState;
  setFormState: (value: PreconsultFormState) => void;
  onSubmit: () => void;
}) {
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <Field label="Cita">
        <select
          aria-label="Cita para preconsulta"
          className="h-9 w-full rounded-md border bg-background px-3 text-sm"
          disabled={disabled}
          value={formState.appointment_id}
          onChange={(event) => setFormState({ ...formState, appointment_id: event.target.value })}
        >
          {appointments.map((appointment) => (
            <option key={appointment.id} value={appointment.id}>
              {formatDateTime(appointment.starts_at)} - {appointment.reason}
            </option>
          ))}
        </select>
      </Field>
      <AppointmentStatusPreview
        appointment={appointments.find((item) => item.id === formState.appointment_id)}
      />
      <Field label="Fecha y hora">
        <Input
          type="datetime-local"
          disabled={disabled}
          value={formState.occurred_at}
          onChange={(event) => setFormState({ ...formState, occurred_at: event.target.value })}
        />
      </Field>
      <Field label="Motivo breve">
        <Input
          disabled={disabled}
          value={formState.chief_complaint}
          onChange={(event) =>
            setFormState({ ...formState, chief_complaint: event.target.value })
          }
        />
      </Field>
      <Field label="Prioridad textual">
        <select
          aria-label="Prioridad de preconsulta"
          className="h-9 w-full rounded-md border bg-background px-3 text-sm"
          disabled={disabled}
          value={formState.triage_priority}
          onChange={(event) =>
            setFormState({
              ...formState,
              triage_priority: event.target.value as PreconsultPriority,
            })
          }
        >
          {Object.entries(priorityLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </Field>
      <VitalsGrid disabled={disabled} formState={formState} setFormState={setFormState} />
      <div className="grid gap-2">
        <CheckField
          checked={formState.identity_checked}
          disabled={disabled}
          label="Identidad local verificada"
          onChange={(checked) => setFormState({ ...formState, identity_checked: checked })}
        />
        <CheckField
          checked={formState.allergies_reviewed}
          disabled={disabled}
          label="Alergias revisadas"
          onChange={(checked) => setFormState({ ...formState, allergies_reviewed: checked })}
        />
        <CheckField
          checked={formState.medications_reviewed}
          disabled={disabled}
          label="Medicacion revisada"
          onChange={(checked) => setFormState({ ...formState, medications_reviewed: checked })}
        />
      </div>
      <Field label="Faltantes">
        <Textarea
          disabled={disabled}
          value={formState.missing_data}
          onChange={(event) => setFormState({ ...formState, missing_data: event.target.value })}
        />
      </Field>
      <Field label="Accion humana">
        <Input
          disabled={disabled}
          value={formState.human_action}
          onChange={(event) => setFormState({ ...formState, human_action: event.target.value })}
        />
      </Field>
      <Button type="submit" disabled={disabled || !formState.appointment_id}>
        {disabled ? <ClipboardCheck className="h-4 w-4" /> : <Save className="h-4 w-4" />}
        Registrar preconsulta
      </Button>
    </form>
  );
}

export function emptyPreconsultForm(): PreconsultFormState {
  return {
    appointment_id: "",
    occurred_at: toDatetimeLocal(new Date()),
    identity_checked: false,
    chief_complaint: "",
    triage_priority: "unknown",
    allergies_reviewed: false,
    medications_reviewed: false,
    missing_data: "",
    human_action: "Revisar en atencion",
    temperature_c: "",
    systolic_bp: "",
    diastolic_bp: "",
    heart_rate_bpm: "",
    respiratory_rate_bpm: "",
    oxygen_saturation_pct: "",
  };
}

function AppointmentStatusPreview({ appointment }: { appointment?: ClinicalAppointment }) {
  if (!appointment) return null;
  return (
    <div className="rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span>{appointment.location_label || "Ubicacion pendiente"}</span>
        <Badge variant="outline">{statusLabels[appointment.status]}</Badge>
      </div>
      <p className="mt-1">{appointment.clinician_label || "Profesional/equipo pendiente"}</p>
    </div>
  );
}

function VitalsGrid({
  disabled,
  formState,
  setFormState,
}: {
  disabled: boolean;
  formState: PreconsultFormState;
  setFormState: (value: PreconsultFormState) => void;
}) {
  const fields: Array<[keyof PreconsultFormState, string]> = [
    ["temperature_c", "Temperatura C"],
    ["systolic_bp", "Sistolica"],
    ["diastolic_bp", "Diastolica"],
    ["heart_rate_bpm", "FC"],
    ["respiratory_rate_bpm", "FR"],
    ["oxygen_saturation_pct", "Sat O2"],
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {fields.map(([key, label]) => (
        <Field key={key} label={label}>
          <Input
            inputMode="decimal"
            disabled={disabled}
            value={String(formState[key])}
            onChange={(event) => setFormState({ ...formState, [key]: event.target.value })}
          />
        </Field>
      ))}
    </div>
  );
}

function CheckField({
  checked,
  disabled,
  label,
  onChange,
}: {
  checked: boolean;
  disabled: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        className="h-4 w-4 rounded border"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      {label}
    </label>
  );
}
