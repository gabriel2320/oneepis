"use client";

import Link from "next/link";
import { ClipboardList } from "lucide-react";

import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PatientRecordSnapshot } from "@/lib/types";

export function StructuredAntecedentsReadModel({
  record,
  patientId,
}: {
  record: PatientRecordSnapshot;
  patientId: string;
}) {
  const hasAntecedents =
    record.active_problems.length > 0 ||
    record.active_allergies.length > 0 ||
    record.active_medications.length > 0;

  if (!hasAntecedents) {
    return (
      <EmptyState
        title="Sin antecedentes estructurados"
        description="Problemas, alergias y medicacion se cargan en sus modulos fuente."
      />
    );
  }

  return (
    <div className="grid gap-3 lg:grid-cols-3">
      <AntecedentColumn
        title="Problemas"
        source="active_problem"
        count={record.active_problems.length}
        href={`/pacientes/${patientId}/problemas`}
        items={record.active_problems.map((problem) => ({
          id: problem.id,
          title: problem.title,
          detail: [problem.code_system, problem.code].filter(Boolean).join(" ") || "Sin codigo",
          meta: `Inicio: ${problem.onset_date ?? "sin fecha"}`,
        }))}
      />
      <AntecedentColumn
        title="Alergias"
        source="allergy"
        count={record.active_allergies.length}
        href={`/pacientes/${patientId}/alergias`}
        items={record.active_allergies.map((allergy) => ({
          id: allergy.id,
          title: allergy.substance,
          detail: allergy.reaction ?? "Reaccion no documentada",
          meta: `Severidad: ${allergy.severity}`,
          warning: allergy.severity === "severe",
        }))}
      />
      <AntecedentColumn
        title="Medicacion"
        source="medication"
        count={record.active_medications.length}
        href={`/pacientes/${patientId}/medicacion`}
        items={record.active_medications.map((medication) => ({
          id: medication.id,
          title: medication.name,
          detail:
            [medication.dose, medication.route, medication.frequency].filter(Boolean).join(" / ") ||
            "Detalle pendiente",
          meta: `Inicio: ${medication.started_on ?? "sin fecha"}`,
        }))}
      />
    </div>
  );
}

function AntecedentColumn({
  title,
  source,
  count,
  href,
  items,
}: {
  title: string;
  source: string;
  count: number;
  href: string;
  items: { id: string; title: string; detail: string; meta: string; warning?: boolean }[];
}) {
  return (
    <section className="rounded-md border bg-card p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-semibold">
            <ClipboardList className="h-4 w-4 text-primary" />
            {title}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">Fuente: {source}</p>
        </div>
        <Badge variant={count > 0 ? "safe" : "outline"}>{count}</Badge>
      </div>
      {items.length > 0 ? (
        <div className="mt-3 space-y-2">
          {items.slice(0, 3).map((item) => (
            <div key={item.id} className="rounded-md border bg-muted/20 p-2">
              <p className="text-sm font-medium">{item.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">{item.detail}</p>
              <p className="mt-1 text-xs text-muted-foreground">{item.meta}</p>
              {item.warning ? (
                <Badge className="mt-2" variant="warning">
                  Alerta
                </Badge>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">Sin registros activos.</p>
      )}
      <Button asChild variant="outline" size="sm" className="mt-3 w-full" data-print-hidden="true">
        <Link href={href}>Abrir fuente</Link>
      </Button>
    </section>
  );
}
