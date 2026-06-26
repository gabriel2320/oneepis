"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GitBranch, Plus } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState } from "@/components/clinical/states";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createClinicalEvent,
  listClinicalEncounters,
  listClinicalEvents,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { demoEncounters } from "@/lib/demo-record";
import { canManageClinicalEvents } from "@/lib/permissions";
import type { ClinicalEventType } from "@/lib/types";

import { BackLink, Field, PageTitle, emptyToNull, toDatetimeLocal, usePatientId, usePatientRecordQuery } from "./patient-page-shared";
import {
  PatientEventCurationPanel,
  PatientEventList,
  type PatientEventCurationPreset,
} from "./patient-event-sections";

const eventTypeOptions: { value: ClinicalEventType; label: string }[] = [
  { value: "symptom", label: "Sintoma" },
  { value: "vital_sign", label: "Signo vital" },
  { value: "exam_result", label: "Resultado examen" },
  { value: "diagnosis", label: "Diagnostico" },
  { value: "medication", label: "Medicamento" },
  { value: "procedure", label: "Procedimiento" },
  { value: "clinical_note", label: "Nota clinica" },
  { value: "care_plan", label: "Plan de cuidado" },
  { value: "administrative", label: "Administrativo" },
];

export function PatientEventsPage() {
  const patientId = usePatientId();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWriteEvents = canManageClinicalEvents(user);
  const [form, setForm] = useState({
    event_type: eventTypeFromQuery(searchParams.get("eventType")),
    occurred_at: toDatetimeLocal(new Date()),
    summary: searchParams.get("summary")?.slice(0, 280) ?? "",
    encounter_id: "",
    details: searchParams.get("details")?.slice(0, 1200) ?? "",
    source_ref: searchParams.get("aiActionId")?.slice(0, 160) ?? "",
    antecedent: null as PatientEventCurationPreset["antecedent"] | null,
  });
  const eventsQuery = useQuery({
    queryKey: ["clinical-events", patientId],
    queryFn: () => listClinicalEvents(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const encountersQuery = useQuery({
    queryKey: ["clinical-encounters", patientId],
    queryFn: () => listClinicalEncounters(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const encounters = DEMO_MODE
    ? demoEncounters.filter((encounter) => encounter.patient_id === patientId)
    : (encountersQuery.data ?? []);
  const createMutation = useMutation({
    mutationFn: () =>
      createClinicalEvent(patientId, {
        event_type: form.event_type,
        occurred_at: new Date(form.occurred_at).toISOString(),
        summary: form.summary,
        encounter_id: emptyToNull(form.encounter_id),
        source_type: form.source_ref ? "ai_draft" : "manual",
        source_ref: emptyToNull(form.source_ref),
        payload: buildEventPayload({
          details: form.details,
          sourceRef: form.source_ref,
          antecedent: form.antecedent,
        }),
      }),
    onSuccess: async () => {
      setForm((current) => ({
        ...current,
        summary: "",
        details: "",
        antecedent: null,
        occurred_at: toDatetimeLocal(new Date()),
      }));
      await queryClient.invalidateQueries({ queryKey: ["clinical-events", patientId] });
    },
  });

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl p-4 md:p-6">
          <ErrorState description="No se pudo cargar el paciente para eventos clinicos." />
        </div>
      </AppShell>
    );
  }

  return (
    <PatientClinicalShell record={record} activeSection="eventos">
      <div className="space-y-5">
        <BackLink href={`/pacientes/${patientId}/ficha`} label="Ficha" />
        <PageTitle
          title="Eventos clinicos"
          description="Ledger de hechos clinicos para alimentar contexto, timeline y borradores."
          action={
            <Button asChild size="sm" variant="outline">
              <Link href={`/pacientes/${patientId}/ai-chart`}>
                <GitBranch className="h-4 w-4" />
                Abrir AI-Chart
              </Link>
            </Button>
          }
        />
        {DEMO_MODE ? <ErrorState description="El modo demo no permite guardar eventos reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWriteEvents ? (
          <ErrorState description="Tu perfil no tiene permiso para registrar eventos clinicos." />
        ) : null}
        <div className="grid gap-4 xl:grid-cols-[420px_minmax(0,1fr)]">
          <ClinicalSectionCard title="Nuevo evento" description="Registra un hecho, no una pantalla completa.">
            {form.source_ref ? (
              <div className="mb-4 rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
                Formulario prellenado desde AI-Chart. Revisa y edita antes de guardar.
              </div>
            ) : null}
            <PatientEventCurationPanel
              disabled={DEMO_MODE || !canWriteEvents}
              onPresetSelect={(preset) =>
                setForm((current) => ({
                  ...current,
                  event_type: preset.event_type,
                  summary: current.summary.trim() ? current.summary : preset.summary,
                  details: current.details.trim() ? current.details : preset.details,
                  antecedent: preset.antecedent,
                }))
              }
            />
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                createMutation.mutate();
              }}
            >
              <Field label="Tipo">
                <select
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                  value={form.event_type}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      event_type: event.target.value as ClinicalEventType,
                    }))
                  }
                >
                  {eventTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Fecha y hora">
                <Input
                  type="datetime-local"
                  value={form.occurred_at}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, occurred_at: event.target.value }))
                  }
                />
              </Field>
              <Field label="Encuentro">
                <select
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                  value={form.encounter_id}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, encounter_id: event.target.value }))
                  }
                >
                  <option value="">Sin encuentro vinculado</option>
                  {encounters.map((encounter) => (
                    <option key={encounter.id} value={encounter.id}>
                      {encounter.reason} - {encounter.type}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Resumen">
                <Input
                  value={form.summary}
                  maxLength={280}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, summary: event.target.value }))
                  }
                />
              </Field>
              <Field label="Detalle estructurable">
                <Textarea
                  className="min-h-24"
                  value={form.details}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, details: event.target.value }))
                  }
                />
              </Field>
              <Button
                type="submit"
                disabled={
                  createMutation.isPending ||
                  DEMO_MODE ||
                  !canWriteEvents ||
                  form.summary.trim().length === 0
                }
              >
                <Plus className="h-4 w-4" />
                {createMutation.isPending ? "Guardando..." : "Guardar evento"}
              </Button>
              {createMutation.isError ? (
                <p className="text-sm text-destructive">No se pudo guardar el evento.</p>
              ) : null}
            </form>
          </ClinicalSectionCard>

          <ClinicalSectionCard title="Timeline de eventos" description="Fuente nueva para AI-Chart Core.">
            <PatientEventList events={eventsQuery.data ?? []} />
            {eventsQuery.isError ? (
              <p className="mt-3 text-sm text-destructive">No se pudieron cargar eventos.</p>
            ) : null}
          </ClinicalSectionCard>
        </div>
      </div>
    </PatientClinicalShell>
  );
}

function eventTypeFromQuery(value: string | null): ClinicalEventType {
  const allowed = new Set(eventTypeOptions.map((option) => option.value));
  return allowed.has(value as ClinicalEventType) ? (value as ClinicalEventType) : "clinical_note";
}

function buildEventPayload({
  details,
  sourceRef,
  antecedent,
}: {
  details: string;
  sourceRef: string;
  antecedent: PatientEventCurationPreset["antecedent"] | null;
}) {
  return {
    ...(emptyToNull(details) ? { details } : {}),
    ...(antecedent ? { antecedent } : {}),
    prefilled_from_ai_action: Boolean(sourceRef),
  };
}
