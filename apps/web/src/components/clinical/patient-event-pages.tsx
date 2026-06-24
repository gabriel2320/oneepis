"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GitBranch, Plus } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { EmptyState, ErrorState } from "@/components/clinical/states";
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
import type { ClinicalEvent, ClinicalEventSourceType, ClinicalEventType } from "@/lib/types";

import {
  BackLink,
  EncounterLinkNotice,
  Field,
  PageTitle,
  emptyToNull,
  toDatetimeLocal,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

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

const sourceTypeOptions: { value: ClinicalEventSourceType; label: string }[] = [
  { value: "manual", label: "Manual" },
  { value: "clinical_entry", label: "Evolucion" },
  { value: "vital_sign", label: "Signo vital" },
  { value: "imported_document", label: "Documento importado" },
  { value: "ai_draft", label: "Borrador IA" },
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
    source_type: searchParams.get("aiActionId") ? "ai_draft" : "manual",
    source_ref: searchParams.get("aiActionId")?.slice(0, 160) ?? "",
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
  const hasSourceRef = form.source_ref.trim().length > 0;
  const createMutation = useMutation({
    mutationFn: () =>
      createClinicalEvent(patientId, {
        event_type: form.event_type,
        occurred_at: new Date(form.occurred_at).toISOString(),
        summary: form.summary,
        encounter_id: emptyToNull(form.encounter_id),
        source_type: form.source_type as ClinicalEventSourceType,
        source_ref: emptyToNull(form.source_ref),
        payload: emptyToNull(form.details)
          ? {
              details: form.details,
              prefilled_from_ai_action: Boolean(form.source_ref),
            }
          : { prefilled_from_ai_action: Boolean(form.source_ref) },
      }),
    onSuccess: async () => {
      setForm((current) => ({
        ...current,
        summary: "",
        details: "",
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
          <ErrorState description="Tu rol actual no permite registrar eventos clinicos." />
        ) : null}
        <div className="grid gap-4 xl:grid-cols-[420px_minmax(0,1fr)]">
          <ClinicalSectionCard title="Nuevo evento" description="Registra un hecho, no una pantalla completa.">
            {form.source_ref ? (
              <div className="mb-4 rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
                Formulario prellenado desde AI-Chart. Revisa y edita antes de guardar.
              </div>
            ) : null}
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
              <EncounterLinkNotice
                hasEncounters={encounters.length > 0}
                hasSelectedEncounter={Boolean(form.encounter_id)}
              />
              <Field label="Fuente">
                <select
                  className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                  value={form.source_type}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      source_type: event.target.value as ClinicalEventSourceType,
                      source_ref: event.target.value === "manual" ? "" : current.source_ref,
                    }))
                  }
                >
                  {sourceTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              {form.source_type !== "manual" ? (
                <Field label="Referencia fuente">
                  <Input
                    value={form.source_ref}
                    maxLength={160}
                    placeholder="ID de evolucion, signo vital, documento o accion IA"
                    onChange={(event) =>
                      setForm((current) => ({ ...current, source_ref: event.target.value }))
                    }
                  />
                </Field>
              ) : null}
              <SourceTraceNotice
                sourceType={form.source_type as ClinicalEventSourceType}
                hasSourceRef={hasSourceRef}
              />
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
            <EventList events={eventsQuery.data ?? []} />
            {eventsQuery.isError ? (
              <p className="mt-3 text-sm text-destructive">No se pudieron cargar eventos.</p>
            ) : null}
          </ClinicalSectionCard>
        </div>
      </div>
    </PatientClinicalShell>
  );
}

function EventList({ events }: { events: ClinicalEvent[] }) {
  if (events.length === 0) {
    return (
      <EmptyState
        title="Sin eventos registrados"
        description="Registra sintomas, hallazgos, resultados o planes para construir contexto clinico."
      />
    );
  }

  return (
    <div className="space-y-3">
      {events.map((event) => (
        <article key={event.id} className="rounded-md border p-3">
          <div className="flex flex-col gap-1 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="font-medium">{event.summary}</p>
              <p className="text-xs text-muted-foreground">
                {event.event_type} - {formatDate(event.occurred_at)}
              </p>
            </div>
            <div className="text-xs text-muted-foreground md:text-right">
              <p>Fuente: {sourceTypeLabel(event.source_type)}</p>
              {event.source_ref ? <p>Ref: {event.source_ref}</p> : null}
              {event.encounter_id ? <p>Encuentro: {event.encounter_id}</p> : null}
            </div>
          </div>
          {typeof event.payload.details === "string" ? (
            <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
              {event.payload.details}
            </p>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function SourceTraceNotice({
  sourceType,
  hasSourceRef,
}: {
  sourceType: ClinicalEventSourceType;
  hasSourceRef: boolean;
}) {
  if (sourceType === "manual") {
    return (
      <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
        Fuente manual: este evento nace del registro humano actual.
      </div>
    );
  }

  if (hasSourceRef) {
    return (
      <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
        Fuente derivada con referencia: el evento conserva su origen para auditoria y timeline.
      </div>
    );
  }

  return (
    <div className="rounded-md border border-warning/40 bg-warning/10 p-3 text-sm text-muted-foreground">
      Fuente derivada sin referencia: agrega el ID de la evolucion, signo, documento o accion IA que origina este evento.
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("es-CL", { dateStyle: "short", timeStyle: "short" });
}

function sourceTypeLabel(value: ClinicalEventSourceType) {
  return sourceTypeOptions.find((option) => option.value === value)?.label ?? value;
}

function eventTypeFromQuery(value: string | null): ClinicalEventType {
  const allowed = new Set(eventTypeOptions.map((option) => option.value));
  return allowed.has(value as ClinicalEventType) ? (value as ClinicalEventType) : "clinical_note";
}
