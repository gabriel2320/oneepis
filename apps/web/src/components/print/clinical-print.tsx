"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { formatDateTime } from "@/components/clinical/date-format";
import { ClinicalTimeline } from "@/components/clinical/patient-widgets";
import { Button } from "@/components/ui/button";
import { DEMO_MODE } from "@/lib/api/client";
import { listHospitalDailySheets } from "@/lib/api/hospitalization";
import { getPatientRecord } from "@/lib/api/patients";
import { demoHospitalDailySheets, demoRecords } from "@/lib/demo-record";
import type { ClinicalEntry, HospitalDailySheet, PatientRecordSnapshot } from "@/lib/types";

export function PrintPatientPage({ kind }: { kind: "ficha" | "resumen" | "receta" }) {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const record =
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) ?? demoRecords[0] : null) ??
    recordQuery.data;

  return (
    <PrintPage>
      <PrintToolbar />
      {record ? (
        kind === "receta" ? (
          <PrescriptionA5Sheet record={record} />
        ) : (
          <PatientSummaryPrintSheet record={record} title={kind === "ficha" ? "Ficha clinica" : "Resumen"} />
        )
      ) : (
        <p className="p-6 text-sm">Cargando documento...</p>
      )}
    </PrintPage>
  );
}

export function PrintEvolutionPage() {
  const params = useParams<{ patientId: string; entryId: string }>();
  const patientId = params.patientId;
  const entryId = params.entryId;
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const record =
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) ?? demoRecords[0] : null) ??
    recordQuery.data;
  const entry = record?.recent_entries.find((item) => item.id === entryId) ?? record?.recent_entries[0];

  return (
    <PrintPage>
      <PrintToolbar />
      {record && entry ? (
        <SoapPrintSheet record={record} entry={entry} />
      ) : (
        <p className="p-6 text-sm">Cargando evolucion...</p>
      )}
    </PrintPage>
  );
}

export function PrintHospitalDailySheetPage() {
  const params = useParams<{ patientId: string; sheetId: string }>();
  const patientId = params.patientId;
  const sheetId = params.sheetId;
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const sheetsQuery = useQuery({
    queryKey: ["hospital-daily-sheets", patientId],
    queryFn: () => listHospitalDailySheets(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const record =
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) ?? demoRecords[0] : null) ??
    recordQuery.data;
  const sheets = DEMO_MODE
    ? demoHospitalDailySheets.filter((item) => item.patient_id === patientId)
    : (sheetsQuery.data ?? []);
  const sheet = sheets.find((item) => item.id === sheetId) ?? sheets[0];

  return (
    <PrintPage>
      <PrintToolbar />
      {record && sheet ? (
        <HospitalDailyPrintSheet record={record} sheet={sheet} />
      ) : (
        <p className="p-6 text-sm">Cargando hoja diaria...</p>
      )}
    </PrintPage>
  );
}

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

export function PatientSummaryPrintSheet({
  record,
  title,
}: {
  record: PatientRecordSnapshot;
  title: string;
}) {
  return (
    <ClinicalPaperSheet record={record} title={title}>
      <section className="print-section">
        <h2 className="text-sm font-semibold">Identificacion</h2>
        <p className="mt-2 text-sm">
          {record.patient.first_name} {record.patient.last_name} - {record.patient.birth_date}
        </p>
      </section>
      <section className="print-section">
        <h2 className="text-sm font-semibold">Alergias</h2>
        <p className="mt-2 text-sm">
          {record.active_allergies.map((item) => item.substance).join(", ") || "Sin alergias activas"}
        </p>
      </section>
      <section className="print-section">
        <h2 className="text-sm font-semibold">Medicacion activa</h2>
        <p className="mt-2 text-sm">
          {record.active_medications.map((item) => item.name).join(", ") || "Sin medicacion activa"}
        </p>
      </section>
      <section className="print-section">
        <h2 className="mb-3 text-sm font-semibold">Evoluciones recientes</h2>
        <ClinicalTimeline entries={record.recent_entries} />
      </section>
      <section className="print-section rounded-md border border-info/30 bg-info/10 p-3">
        <h2 className="text-sm font-semibold">Resumen IA</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          No se imprime contenido IA persistido. Las sugerencias Ollama son borradores y no sustituyen
          texto clinico firmado.
        </p>
      </section>
    </ClinicalPaperSheet>
  );
}

export function PrescriptionA5Sheet({ record }: { record: PatientRecordSnapshot }) {
  return (
    <article className="print-sheet mx-auto min-h-[210mm] max-w-[148mm] border bg-card p-6 shadow-sm">
      <PrintHeader record={record} title="Receta" />
      <div className="space-y-5 py-6">
        <section className="print-section rounded-md border border-warning/40 bg-warning/10 p-3">
          <h2 className="text-sm font-semibold">Prescripcion no habilitada</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Requiere autenticacion, permisos, firma profesional y politica de prescripcion.
          </p>
        </section>
        <section className="print-section">
          <h2 className="text-sm font-semibold">Paciente</h2>
          <p className="mt-2 text-sm">
            {record.patient.first_name} {record.patient.last_name}
          </p>
        </section>
        <section className="print-section min-h-32 border-t pt-4">
          <p className="text-sm text-muted-foreground">
            Firma profesional: _________________________
          </p>
        </section>
      </div>
      <PrintFooter />
    </article>
  );
}

export function SoapPrintSheet({
  record,
  entry,
}: {
  record: PatientRecordSnapshot;
  entry: ClinicalEntry;
}) {
  return (
    <ClinicalPaperSheet record={record} title="Evolucion SOAP">
      <section className="print-section space-y-3">
        <div>
          <h2 className="text-sm font-semibold">{entry.title}</h2>
          <p className="text-xs text-muted-foreground">{formatDateTime(entry.occurred_at)}</p>
        </div>
        <SoapRow label="S" value={entry.subjective} />
        <SoapRow label="O" value={entry.objective} />
        <SoapRow label="A" value={entry.assessment} />
        <SoapRow label="P" value={entry.plan} />
      </section>
    </ClinicalPaperSheet>
  );
}

export function HospitalDailyPrintSheet({
  record,
  sheet,
}: {
  record: PatientRecordSnapshot;
  sheet: HospitalDailySheet;
}) {
  return (
    <ClinicalPaperSheet record={record} title="Hoja diaria hospitalizada">
      <section className="print-section space-y-3">
        <div>
          <h2 className="text-sm font-semibold">Fecha {sheet.sheet_date}</h2>
          <p className="text-xs text-muted-foreground">
            Registrada por {sheet.created_by} - {formatDateTime(sheet.created_at)}
          </p>
        </div>
        <PrintTextBlock label="Resumen clinico" value={sheet.clinical_summary} />
        <PrintTextBlock label="Eventos relevantes" value={sheet.overnight_events} />
        <PrintTextBlock label="Plan activo" value={sheet.active_plan} />
        <PrintTextBlock label="Pendientes" value={sheet.pending_tasks} />
        <PrintTextBlock label="Notas de seguridad" value={sheet.safety_notes} />
      </section>
    </ClinicalPaperSheet>
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

function SoapRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm">{value || "Sin registro"}</p>
    </div>
  );
}

function PrintTextBlock({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-sm">{value || "Sin registro"}</p>
    </div>
  );
}
