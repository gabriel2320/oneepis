import { ClipboardList } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ClinicalEntry } from "@/lib/types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function ClinicalTimeline({ entries }: { entries: ClinicalEntry[] }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <ClipboardList className="h-4 w-4" />
          Evolución clínica
        </CardTitle>
        <Badge variant="secondary">{entries.length} registros</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.length === 0 ? (
          <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
            Aún no hay entradas clínicas para este paciente demo.
          </div>
        ) : (
          entries.map((entry) => (
            <article key={entry.id} className="rounded-md border bg-background p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-sm font-semibold">{entry.title}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">{formatDate(entry.occurred_at)}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{entry.kind}</Badge>
                  <Badge variant={entry.status === "signed" ? "safe" : "warning"}>{entry.status}</Badge>
                </div>
              </div>
              <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
                <ClinicalBlock label="S" value={entry.subjective} />
                <ClinicalBlock label="O" value={entry.objective} />
                <ClinicalBlock label="A" value={entry.assessment} />
                <ClinicalBlock label="P" value={entry.plan} />
              </div>
            </article>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function ClinicalBlock({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex gap-2 rounded-md bg-muted/60 p-3">
      <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-card text-xs font-semibold">
        {label}
      </div>
      <p className="min-w-0 text-muted-foreground">{value || "Sin contenido"}</p>
    </div>
  );
}
