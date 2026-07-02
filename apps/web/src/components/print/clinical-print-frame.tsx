import type { ReactNode } from "react";

import { careContextLabel, clinicalStatusLabel } from "@/lib/patient-display";
import type { PatientRecordSnapshot } from "@/lib/types";

type ClinicalPaperMetadata = {
  source: string;
  status: string;
  actor?: string | null;
  clinicalDate?: string | null;
};

export function PrintPage({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-muted/40 p-4 print:bg-white print:p-0">{children}</main>;
}

export function ClinicalPaperSheet({
  record,
  title,
  metadata,
  children,
}: {
  record: PatientRecordSnapshot;
  title: string;
  metadata?: ClinicalPaperMetadata;
  children: ReactNode;
}) {
  return (
    <article className="print-sheet mx-auto min-h-[279mm] max-w-3xl border bg-card p-8 shadow-sm print:min-h-[250mm]">
      <PrintHeader record={record} title={title} />
      {metadata ? <PrintDocumentMetadata metadata={metadata} /> : null}
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
          <p className="text-muted-foreground">No PHI / no uso clinico real</p>
        </div>
      </div>
      <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
        <p>Fecha nacimiento: {record.patient.birth_date ?? "Sin registro"}</p>
        <p>Estado ficha: {clinicalStatusLabel(record.patient.clinical_status)}</p>
        <p>Contexto: {careContextLabel(record.patient.current_care_context)}</p>
      </div>
    </header>
  );
}

function PrintDocumentMetadata({ metadata }: { metadata: ClinicalPaperMetadata }) {
  return (
    <section className="mt-4 rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
      <p className="font-semibold text-foreground">Metadata documental</p>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <p>Fuente: {metadata.source}</p>
        <p>Estado: {metadata.status}</p>
        <p>Actor: {metadata.actor || "No registrado"}</p>
        <p>Fecha clinica: {metadata.clinicalDate || "No registrada"}</p>
      </div>
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
        <p>Folio demo: ONE-DEV - Pagina 1</p>
      </div>
      <p className="mt-1 font-semibold">Documento de desarrollo / no PHI / no uso clinico real.</p>
    </footer>
  );
}
