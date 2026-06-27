"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { listPatientAppointments, updatePatientAppointment } from "@/lib/api/appointments";
import {
  createClinicalEncounter,
  createClinicalEvent,
  createVitalSign,
} from "@/lib/api/clinical-record";
import { AMBULATORY_PRECONSULT_WORKFLOW } from "@/lib/ambulatory-workflows";
import { DEMO_MODE } from "@/lib/api/client";
import { demoAppointments } from "@/lib/demo-record";
import {
  canManageClinicalEvents,
  canManagePreconsult,
  canRecordVitals,
} from "@/lib/permissions";
import type { AppointmentStatus, ClinicalAppointment } from "@/lib/types";

import {
  PreconsultForm,
  emptyPreconsultForm,
  type PreconsultFormState,
} from "./ambulatory-preconsult-form";
import { emptyToNull, numberOrNull } from "./patient-page-shared";

export function AmbulatoryPreconsultPanel({ patientId }: { patientId: string }) {
  const queryClient = useQueryClient();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite =
    canManagePreconsult(user) && canManageClinicalEvents(user) && canRecordVitals(user);
  const appointmentsQuery = useQuery({
    queryKey: ["patient-appointments", patientId, "preconsult"],
    queryFn: () => listPatientAppointments(patientId),
    enabled: !DEMO_MODE,
  });
  const appointments = useMemo(
    () =>
      (DEMO_MODE
        ? demoAppointments.filter((appointment) => appointment.patient_id === patientId)
        : appointmentsQuery.data ?? []
      ).filter((appointment) => preconsultableStatuses.has(appointment.status)),
    [appointmentsQuery.data, patientId],
  );
  const [formState, setFormState] = useState<PreconsultFormState>(emptyPreconsultForm);
  const selectedAppointmentId = formState.appointment_id || appointments[0]?.id || "";
  const selectedAppointment = appointments.find(
    (appointment) => appointment.id === selectedAppointmentId,
  );
  const mutation = useMutation({
    mutationFn: (payload: PreconsultFormState) =>
      createPreconsult(patientId, payload, selectedAppointment),
    onSuccess: async () => {
      setFormState(emptyPreconsultForm());
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["clinical-encounters", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["patient-appointments", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["appointments"] }),
      ]);
    },
  });
  const disabled =
    mutation.isPending ||
    DEMO_MODE ||
    !canWrite ||
    userLoading ||
    appointments.length === 0 ||
    appointmentsQuery.isLoading;

  return (
    <details className="rounded-md border bg-card">
      <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-foreground">
        Preconsulta ambulatoria
      </summary>
      <div className="space-y-3 border-t px-3 pb-3 pt-2">
        <p className="text-xs text-muted-foreground">
          Check-in clinico minimo antes de la atencion. No emite diagnostico, receta, orden ni firma.
        </p>
        {appointmentsQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={2} /> : null}
        {appointmentsQuery.isError && !DEMO_MODE ? (
          <ErrorState
            description="No se pudieron cargar las citas del paciente."
            onRetry={() => appointmentsQuery.refetch()}
          />
        ) : null}
        {DEMO_MODE ? (
          <p className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
            Modo demo: la preconsulta se muestra como flujo visible y queda bloqueada para escritura.
          </p>
        ) : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <p className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
            Tu perfil no tiene permiso para registrar preconsulta completa.
          </p>
        ) : null}
        {appointments.length === 0 && !appointmentsQuery.isLoading ? (
          <EmptyState
            title="Sin citas para preconsulta"
            description="Agenda una cita o revisa que no este completada, cancelada o no-show."
          />
        ) : null}
        {appointments.length > 0 ? (
          <PreconsultForm
            appointments={appointments}
            disabled={disabled}
            formState={{ ...formState, appointment_id: selectedAppointmentId }}
            setFormState={setFormState}
            onSubmit={() =>
              mutation.mutate({
                ...formState,
                appointment_id: selectedAppointmentId,
                chief_complaint: formState.chief_complaint || selectedAppointment?.reason || "",
              })
            }
          />
        ) : null}
        {mutation.isError ? (
          <p className="text-sm text-destructive">
            No se pudo registrar la preconsulta. Revisa API, permisos y pertenencia de la cita.
          </p>
        ) : null}
        {mutation.data ? (
          <p className="text-sm text-muted-foreground">
            Preconsulta registrada: {mutation.data.summary}
          </p>
        ) : null}
      </div>
    </details>
  );
}

async function createPreconsult(
  patientId: string,
  payload: PreconsultFormState,
  appointment?: ClinicalAppointment,
) {
  if (!appointment) {
    throw new Error("Appointment not found");
  }
  const occurredAt = new Date(payload.occurred_at).toISOString();
  const reason = payload.chief_complaint.trim() || appointment.reason;
  const encounter = await createClinicalEncounter(patientId, {
    type: "ambulatory",
    status: "in_progress",
    workflow_kind: AMBULATORY_PRECONSULT_WORKFLOW,
    reason,
    started_at: occurredAt,
    location_label: appointment.location_label ?? null,
    notes: "Preconsulta vinculada a cita ambulatoria.",
  });
  if (hasAnyVital(payload)) {
    await createVitalSign(patientId, {
      measured_at: occurredAt,
      temperature_c: emptyToNull(payload.temperature_c),
      systolic_bp: optionalNumber(payload.systolic_bp),
      diastolic_bp: optionalNumber(payload.diastolic_bp),
      heart_rate_bpm: optionalNumber(payload.heart_rate_bpm),
      respiratory_rate_bpm: optionalNumber(payload.respiratory_rate_bpm),
      oxygen_saturation_pct: emptyToNull(payload.oxygen_saturation_pct),
      notes: "Signos registrados en preconsulta ambulatoria.",
    });
  }
  const event = await createClinicalEvent(patientId, {
    encounter_id: encounter.id,
    event_type: "clinical_note",
    occurred_at: occurredAt,
    summary: `Preconsulta ambulatoria: ${reason}`,
    source_type: "manual",
    source_ref: `appointment:${appointment.id}`,
    payload: {
      preconsult: {
        appointment_id: appointment.id,
        identity_checked: payload.identity_checked,
        chief_complaint: reason,
        triage_priority: payload.triage_priority,
        allergies_reviewed: payload.allergies_reviewed,
        medications_reviewed: payload.medications_reviewed,
        missing_data: splitLines(payload.missing_data),
        human_action: emptyToNull(payload.human_action),
      },
    },
  });
  await updatePatientAppointment(patientId, appointment.id, { status: "in_progress" });
  return event;
}

function hasAnyVital(payload: PreconsultFormState) {
  return Boolean(
    payload.temperature_c ||
      payload.systolic_bp ||
      payload.diastolic_bp ||
      payload.heart_rate_bpm ||
      payload.respiratory_rate_bpm ||
      payload.oxygen_saturation_pct,
  );
}

function optionalNumber(value: string) {
  return value.trim() ? numberOrNull(value) : null;
}

function splitLines(value: string) {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

const preconsultableStatuses = new Set<AppointmentStatus>([
  "scheduled",
  "check_in",
  "in_progress",
]);
