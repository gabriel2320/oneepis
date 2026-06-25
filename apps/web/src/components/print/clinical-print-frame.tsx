"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import type { PatientRecordSnapshot } from "@/lib/types";

export type PaperTraceabilityItem = {
  label: string;
  value: ReactNode;
};

export type PaperTraceabilityProps = {
  items: PaperTraceabilityItem[];
  limitation: ReactNode;
};

export function PrintPage({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-muted/40 p-4 print:bg-white print:p-0">{children}</main>;
}

export function PrintToolbar() {
  return (
    <div className="mx-auto mb-4 flex max-w-3xl items-center justify-between gap-3" data-print-hidden="true">
      <div>
        <p className="text-sm font-semibold">Vista papel</p>
        <p className="text-xs text-muted-foreground">Hoja carta con footer de desarrollo.</p>
      </div>
      <Button type="button" onClick={() => window.print()}>
        Imprimir
      </Button>
    </div>
  );
}

export function ClinicalPaperSheet({
  record,
  title,
  traceability,
  children,
}: {
  record: PatientRecordSnapshot;
  title: string;
  traceability?: PaperTraceabilityProps;
  children: ReactNode;
}) {
  return (
    <article className="print-sheet mx-auto min-h-[279mm] max-w-3xl border bg-card p-8 shadow-sm print:min-h-[250mm]">
      <PrintHeader record={record} title={title} />
      {traceability ? <PaperTraceability {...traceability} /> : null}
      <div className="space-y-5 py-6">{children}</div>
      <PrintFooter />
    </article>
  );
}

export function PrintHeader({
  record,
  title,
}: {
  record: PatientRecordSnapshot;
  title: string;
}) {
  return (
    <header className="border-b pb-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground">OneEpis</p>
          <h1 className="mt-1 text-2xl font-semibold">{title}</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {record.patient.first_name} {record.patient.last_name} -{" "}
            {record.patient.clinical_identifier ?? record.patient.id}
          </p>
        </div>
        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs">
          <p className="font-semibold uppercase text-warning-foreground">Desarrollo</p>
          <p className="text-muted-foreground">No uso clinico real</p>
        </div>
      </div>
      <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
        <p>Fecha nacimiento: {record.patient.birth_date ?? "Sin registro"}</p>
        <p>Estado ficha: {record.patient.clinical_status}</p>
        <p>Contexto: {record.patient.current_care_context}</p>
      </div>
    </header>
  );
}

export function PaperTraceability({ items, limitation }: PaperTraceabilityProps) {
  return (
    <section className="mt-4 rounded-md border border-info/30 bg-info/10 p-3 text-xs">
      <div className="grid gap-2 sm:grid-cols-2">
        {items.map((item) => (
          <p key={item.label}>
            <span className="font-semibold text-foreground">{item.label}:</span>{" "}
            <span className="text-muted-foreground">{item.value}</span>
          </p>
        ))}
      </div>
      <p className="mt-2 border-t border-info/30 pt-2 font-semibold text-muted-foreground">
        Limite: {limitation}
      </p>
    </section>
  );
}

export function PrintFooter() {
  return (
    <footer className="mt-8 border-t pt-4 text-xs text-muted-foreground">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <p>
          Fecha: <span suppressHydrationWarning>{new Date().toLocaleString("es-CL")}</span>
        </p>
        <p>Folio interno: ONE-DEV - Pagina 1</p>
      </div>
      <p className="mt-1 font-semibold">Documento de desarrollo / no uso clinico real.</p>
    </footer>
  );
}
