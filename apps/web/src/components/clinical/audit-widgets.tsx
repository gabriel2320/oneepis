"use client";

import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import type { AuditEvent } from "@/lib/types";

import { formatDateTime } from "./date-format";

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
    <div className="mb-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
      <Badge variant="secondary">Lectura</Badge>
      <span>accesos de ficha o paciente</span>
      <Badge variant="default">Escritura</Badge>
      <span>cambios clinicos auditados</span>
    </div>
  );
}

export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  if (events.length === 0) {
    return <EmptyState title="Sin eventos de auditoria" description="Las escrituras quedaran trazadas aqui." />;
  }

  return (
    <div className="space-y-2">
      {events.map((event) => {
        const kind = auditEventKind(event.action);
        return (
        <div key={event.id} className="rounded-md border p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold">{event.action}</p>
              {kind === "lectura" ? <Badge variant="secondary">Lectura</Badge> : null}
              {kind === "escritura" ? <Badge variant="default">Escritura</Badge> : null}
            </div>
            <Badge variant="outline">{event.actor_id}</Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {event.entity_type} - {formatDateTime(event.created_at)}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
            {event.correlation_id ? <Badge variant="outline">{event.correlation_id}</Badge> : null}
            {event.request_method && event.request_path ? (
              <span>
                {event.request_method} {event.request_path}
              </span>
            ) : null}
          </div>
          <AuditChangeSummary data={event.extra_data} />
        </div>
        );
      })}
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
