"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import type { PatientRecordSnapshot } from "@/lib/types";

export function PrintPage({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-muted/40 p-4 print:bg-white print:p-0">{children}</main>;
}

export function PrintToolbar() {
  return (
    <div className="mx-auto mb-4 flex max-w-3xl justify-end" data-print-hidden="true">
      <Button type="button" onClick={() => window.print()}>
        Imprimir
      </Button>
    </div>
  );
}

export function ClinicalPaperSheet({
  record,
  title,
  children,
}: {
  record: PatientRecordSnapshot;
  title: string;
  children: ReactNode;
}) {
  return (
    <article className="print-sheet mx-auto min-h-[279mm] max-w-3xl border bg-card p-8 shadow-sm print:min-h-[250mm]">
      <PrintHeader record={record} title={title} />
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
      <p className="text-xs font-semibold uppercase text-muted-foreground">OneEpis</p>
      <h1 className="mt-1 text-2xl font-semibold">{title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {record.patient.first_name} {record.patient.last_name} -{" "}
        {record.patient.clinical_identifier ?? record.patient.id}
      </p>
    </header>
  );
}

export function PrintFooter() {
  return (
    <footer className="mt-8 border-t pt-4 text-xs text-muted-foreground">
      <p>
        Fecha: <span suppressHydrationWarning>{new Date().toLocaleString("es-CL")}</span> - Folio demo:
        ONE-DEV - Pagina 1
      </p>
      <p>Documento de desarrollo / no uso clinico real.</p>
    </footer>
  );
}

export function PrintTextBlock({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-sm">{value || "Sin registro"}</p>
    </div>
  );
}
