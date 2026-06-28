"use client";

import { useMemo, useState } from "react";

import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AuditEvent } from "@/lib/types";

import { formatDateTime } from "./date-format";

type AuditKind = "lectura" | "escritura";
type AuditFilter = "todos" | AuditKind;

export function auditEventKind(action: string): "lectura" | "escritura" | null {
  if (action.endsWith(".read") || action.includes(".read.")) {
    return "lectura";
  }
  if (action.includes(".")) {
    return "escritura";
  }
  return null;
}

export function AuditKindLegend() {
  return (
    <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
      <Badge variant="secondary">Lectura</Badge>
      <span>acceso a ficha o paciente</span>
      <Badge variant="default">Escritura</Badge>
      <span>cambios clinicos auditados</span>
    </div>
  );
}

export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  const [activeFilter, setActiveFilter] = useState<AuditFilter>("todos");
  const { counts, filteredEvents } = useMemo(() => {
    const nextCounts = { todos: events.length, lectura: 0, escritura: 0 };
    for (const event of events) {
      const kind = auditEventKind(event.action);
      if (kind) {
        nextCounts[kind] += 1;
      }
    }
    return {
      counts: nextCounts,
      filteredEvents:
        activeFilter === "todos"
          ? events
          : events.filter((event) => auditEventKind(event.action) === activeFilter),
    };
  }, [activeFilter, events]);

  if (events.length === 0) {
    return (
      <EmptyState
        title="Sin eventos de auditoria"
        description="Cuando la API entregue eventos, se mostraran lecturas y escrituras con actor y ruta."
      />
    );
  }

  return (
    <div className="space-y-3">
      <AuditSummary counts={counts} activeFilter={activeFilter} onFilterChange={setActiveFilter} />
      {filteredEvents.length === 0 ? (
        <EmptyState title="Sin eventos para este filtro" description="Cambia el filtro para revisar otros eventos." />
      ) : null}
      {filteredEvents.map((event) => {
        const kind = auditEventKind(event.action);
        return (
          <div key={event.id} className="rounded-md border p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <p className="break-all text-sm font-semibold">{event.action}</p>
                {kind === "lectura" ? <Badge variant="secondary">Lectura</Badge> : null}
                {kind === "escritura" ? <Badge variant="default">Escritura</Badge> : null}
                {!kind ? <Badge variant="outline">Evento de auditoria</Badge> : null}
              </div>
              <Badge variant="outline">Actor: {event.actor_id}</Badge>
            </div>
            <dl className="mt-2 grid gap-2 text-xs text-muted-foreground md:grid-cols-2">
              <AuditMeta label="Entidad" value={event.entity_type} />
              <AuditMeta label="Fecha" value={formatDateTime(event.created_at)} />
              {event.request_method && event.request_path ? (
                <AuditMeta label="Ruta" value={`${event.request_method} ${event.request_path}`} />
              ) : null}
              {event.correlation_id ? <AuditMeta label="Correlacion" value={event.correlation_id} /> : null}
            </dl>
            <AuditChangeSummary data={event.extra_data} />
          </div>
        );
      })}
    </div>
  );
}

function AuditSummary({
  counts,
  activeFilter,
  onFilterChange,
}: {
  counts: Record<AuditFilter, number>;
  activeFilter: AuditFilter;
  onFilterChange: (filter: AuditFilter) => void;
}) {
  const filters: { value: AuditFilter; label: string }[] = [
    { value: "todos", label: "Todos" },
    { value: "lectura", label: "Lecturas" },
    { value: "escritura", label: "Escrituras" },
  ];

  return (
    <div className="flex flex-col gap-3 rounded-md border bg-muted/30 p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap gap-2 text-xs">
        <AuditCount label="Total" value={counts.todos} />
        <AuditCount label="Lecturas" value={counts.lectura} />
        <AuditCount label="Escrituras" value={counts.escritura} />
      </div>
      <div className="flex flex-wrap gap-2" aria-label="Filtro de eventos de auditoria">
        {filters.map((filter) => (
          <Button
            key={filter.value}
            type="button"
            size="sm"
            variant={activeFilter === filter.value ? "default" : "outline"}
            aria-pressed={activeFilter === filter.value}
            onClick={() => onFilterChange(filter.value)}
          >
            {filter.label} {counts[filter.value]}
          </Button>
        ))}
      </div>
    </div>
  );
}

function AuditCount({ label, value }: { label: string; value: number }) {
  return (
    <span className="rounded-md border bg-background px-2 py-1 font-medium text-foreground">
      {label}: {value}
    </span>
  );
}

function AuditMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="font-medium text-foreground">{label}</dt>
      <dd className="break-all">{value}</dd>
    </div>
  );
}

function AuditChangeSummary({ data }: { data: Record<string, unknown> }) {
  const before = isRecord(data.before) ? data.before : null;
  const after = isRecord(data.after) ? data.after : null;

  if (!before && !after) {
    return null;
  }

  return (
    <div className="mt-2 rounded-md bg-muted/40 p-2 text-xs text-muted-foreground">
      {before ? <p>Antes: {JSON.stringify(before)}</p> : null}
      {after ? <p>Despues: {JSON.stringify(after)}</p> : null}
    </div>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
