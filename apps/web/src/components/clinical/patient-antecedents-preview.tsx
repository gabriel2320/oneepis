"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { getClinicalTimeline } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type { ClinicalEvent, PatientRecordSnapshot } from "@/lib/types";

type AntecedentItem = {
  id: string;
  label: string;
  detail: string;
  source: string;
  href: string;
  occurredAt?: string;
};

const antecedentEventTypes = new Set(["diagnosis", "procedure", "clinical_note", "care_plan"]);

export function PatientAntecedentsPreview({
  patientId,
  record,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
}) {
  const timelineQuery = useQuery({
    queryKey: ["clinical-timeline", patientId, "antecedents-preview"],
    queryFn: () => getClinicalTimeline(patientId),
    enabled: !DEMO_MODE,
  });
  const curatedEvents = (timelineQuery.data?.events ?? [])
    .filter((event) => antecedentEventTypes.has(event.event_type))
    .slice(0, 4);
  const items = buildAntecedentItems(record, patientId, curatedEvents);

  return (
    <ClinicalSectionCard
      title="Antecedentes clinicos"
      description="Lectura minima desde fuentes actuales; no reemplaza antecedentes estructurados."
      action={
        <Link
          className="text-xs font-medium text-primary underline-offset-4 hover:underline"
          href={`/pacientes/${patientId}/eventos`}
        >
          Curar eventos
        </Link>
      }
    >
      {timelineQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {timelineQuery.isError ? (
        <ErrorState
          description="No se pudieron cargar eventos para antecedentes."
          onRetry={() => timelineQuery.refetch()}
        />
      ) : null}
      {items.length === 0 ? (
        <EmptyState
          title="Sin antecedentes visibles"
          description="Registra problemas, alergias, medicacion o eventos clinicos para alimentar esta lectura."
        />
      ) : (
        <div className="space-y-2">
          {items.slice(0, 6).map((item) => (
            <article key={item.id} className="rounded-md border bg-background p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{item.detail}</p>
                </div>
                <Badge variant="outline">{item.source}</Badge>
              </div>
              {item.occurredAt ? (
                <p className="mt-2 text-[11px] text-muted-foreground">
                  Fecha fuente: {formatDateTime(item.occurredAt)}
                </p>
              ) : null}
              <Link
                className="mt-2 inline-flex text-[11px] font-medium text-primary underline-offset-4 hover:underline"
                href={item.href}
              >
                Ver fuente
              </Link>
            </article>
          ))}
        </div>
      )}
      <div className="mt-3 rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
        Faltantes declarados: antecedentes familiares/sociales, vacunas, dispositivos y diagnosticos
        historicos codificados siguen pendientes de contrato propio.
      </div>
    </ClinicalSectionCard>
  );
}

function buildAntecedentItems(
  record: PatientRecordSnapshot,
  patientId: string,
  events: ClinicalEvent[],
): AntecedentItem[] {
  return [
    ...record.active_problems.map((problem) => ({
      id: `problem-${problem.id}`,
      label: problem.title,
      detail: problem.notes ?? `Estado: ${problem.status}`,
      source: "problemas",
      href: `/pacientes/${patientId}/problemas`,
      occurredAt: problem.onset_date ?? undefined,
    })),
    ...record.active_allergies.map((allergy) => ({
      id: `allergy-${allergy.id}`,
      label: allergy.substance,
      detail: allergy.reaction ?? `Severidad: ${allergy.severity}`,
      source: "alergias",
      href: `/pacientes/${patientId}/alergias`,
      occurredAt: allergy.recorded_at,
    })),
    ...record.active_medications.map((medication) => ({
      id: `medication-${medication.id}`,
      label: medication.name,
      detail:
        [medication.dose, medication.route, medication.frequency].filter(Boolean).join(" / ") ||
        `Estado: ${medication.status}`,
      source: "medicacion",
      href: `/pacientes/${patientId}/medicacion`,
      occurredAt: medication.started_on ?? undefined,
    })),
    ...events.map((event) => ({
      id: `event-${event.id}`,
      label: event.summary,
      detail: `Evento curado como ${event.event_type}`,
      source: "clinical_events",
      href: `/pacientes/${patientId}/eventos`,
      occurredAt: event.occurred_at,
    })),
  ].filter((item) => item.detail.trim().length > 0);
}
