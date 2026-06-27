"use client";

import { useMemo, useState } from "react";

import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClinicalEntry } from "@/lib/types";

import { formatDateTime } from "./date-format";

const KIND_LABELS: Record<string, string> = {
  progress: "Evolucion",
  admission: "Ingreso",
  discharge: "Egreso",
  procedure: "Procedimiento",
  note: "Nota",
};

export function ClinicalTimelineFeed({ entries }: { entries: ClinicalEntry[] }) {
  const ordered = useMemo(
    () =>
      entries
        .slice()
        .sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime()),
    [entries],
  );
  const kinds = useMemo(() => Array.from(new Set(ordered.map((entry) => entry.kind))), [ordered]);
  const [activeKind, setActiveKind] = useState<string>("all");
  const visible = activeKind === "all" ? ordered : ordered.filter((entry) => entry.kind === activeKind);

  if (ordered.length === 0) {
    return <EmptyState title="Sin evoluciones" description="Crea una evolucion para iniciar la linea clinica." />;
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2" aria-label="Filtro por tipo">
        <FilterChip label="Todas" count={ordered.length} active={activeKind === "all"} onClick={() => setActiveKind("all")} />
        {kinds.map((kind) => (
          <FilterChip
            key={kind}
            label={kindLabel(kind)}
            count={ordered.filter((entry) => entry.kind === kind).length}
            active={activeKind === kind}
            onClick={() => setActiveKind(kind)}
          />
        ))}
      </div>
      {visible.length === 0 ? (
        <EmptyState title="Sin registros para este tipo" description="Ajusta el filtro para ver mas evoluciones." />
      ) : (
        <ol className="space-y-2">
          {visible.map((entry) => (
            <li key={entry.id} className="rounded-md border bg-background p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium">{entry.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(entry.occurred_at)}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{kindLabel(entry.kind)}</Badge>
                  <Badge variant={entry.status === "signed" ? "safe" : "secondary"}>{entry.status}</Badge>
                </div>
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground">Fuente: {entry.created_by || "Sin registro"}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function FilterChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant={active ? "default" : "outline"}
      className="gap-2"
      aria-pressed={active}
      onClick={onClick}
    >
      {label}
      <span className="text-[11px] opacity-80">{count}</span>
    </Button>
  );
}

function kindLabel(kind: string) {
  return KIND_LABELS[kind] ?? kind;
}
