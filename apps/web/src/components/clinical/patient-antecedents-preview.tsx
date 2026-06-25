"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { getClinicalTimeline } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type { PatientRecordSnapshot } from "@/lib/types";

import {
  buildAntecedentItems,
  categoryLabel,
  isCuratedAntecedentEvent,
  sourceDetails,
  sourceLabels,
  type AntecedentSource,
} from "./patient-antecedents-data";

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
    .filter(isCuratedAntecedentEvent)
    .slice(0, 4);
  const items = buildAntecedentItems(record, patientId, curatedEvents);
  const sourceCounts = {
    problemas: record.active_problems.length,
    alergias: record.active_allergies.length,
    medicacion: record.active_medications.length,
    eventos: curatedEvents.length,
  };

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
      <div className="mb-3 flex flex-wrap gap-2">
        <Badge variant="safe">Solo lectura</Badge>
        <Badge variant="outline">Fuentes actuales</Badge>
        <Badge variant="outline">Sin escritura</Badge>
      </div>
      {timelineQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {timelineQuery.isError ? (
        <ErrorState
          description="No se pudieron cargar eventos para antecedentes."
          onRetry={() => timelineQuery.refetch()}
        />
      ) : null}
      <AntecedentSourceSummary counts={sourceCounts} total={items.length} />
      <AntecedentCategorySummary items={items} />
      {items.length === 0 ? (
        <EmptyState
          title="Sin antecedentes visibles"
          description="Registra problemas, alergias, medicacion o eventos clinicos para alimentar esta lectura."
        />
      ) : (
        <div className="mt-3 space-y-2">
          {items.slice(0, 6).map((item) => (
            <article key={item.id} className="rounded-md border bg-background p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{item.detail}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{item.context}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{categoryLabel(item.category)}</Badge>
                  <Badge variant="outline">{sourceLabels[item.source]}</Badge>
                </div>
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
      {items.length > 6 ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Vista resumida: se muestran 6 de {items.length} fuentes disponibles.
        </p>
      ) : null}
      <AntecedentMissingDataNotice />
    </ClinicalSectionCard>
  );
}

function AntecedentCategorySummary({
  items,
}: {
  items: ReturnType<typeof buildAntecedentItems>;
}) {
  const counts = items.reduce<Record<string, number>>((accumulator, item) => {
    accumulator[item.category] = (accumulator[item.category] ?? 0) + 1;
    return accumulator;
  }, {});
  const entries = Object.entries(counts);
  if (entries.length === 0) {
    return null;
  }
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {entries.map(([category, count]) => (
        <Badge key={category} variant="outline">
          {categoryLabel(category)}: {count}
        </Badge>
      ))}
    </div>
  );
}

function AntecedentSourceSummary({
  counts,
  total,
}: {
  counts: Record<"problemas" | "alergias" | "medicacion" | "eventos", number>;
  total: number;
}) {
  return (
    <div className="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium text-foreground">Fuentes usadas</p>
        <Badge variant={total > 0 ? "safe" : "warning"}>{total} visibles</Badge>
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-2">
        {Object.entries(sourceLabels).map(([source, label]) => (
          <div key={source} className="rounded-md border bg-background p-2">
            <p className="font-medium text-foreground">
              {label}: {counts[source as AntecedentSource]}
            </p>
            <p className="mt-1">{sourceDetails[source as AntecedentSource]}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function AntecedentMissingDataNotice() {
  return (
    <div className="mt-3 rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
      <p className="font-medium text-foreground">Faltantes declarados</p>
      <p className="mt-1">
        Familiares/sociales, vacunas, dispositivos y diagnosticos historicos codificados
        siguen pendientes de contrato propio. Esta lectura no crea ni corrige antecedentes
        estructurados.
      </p>
    </div>
  );
}
