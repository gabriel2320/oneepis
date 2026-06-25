"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { formatClinicalEntryStatus } from "@/components/clinical/clinical-entry-labels";
import { formatDateTime } from "@/components/clinical/date-format";
import { ClinicalTimeline } from "@/components/clinical/patient-widgets";
import { DEMO_MODE } from "@/lib/api/client";
import { getPatientRecord } from "@/lib/api/patients";
import { demoRecords } from "@/lib/demo-record";
import type { ClinicalEntry, PatientRecordSnapshot } from "@/lib/types";

import { PrescriptionA5Sheet } from "./blocked-prescription-print";
import { ClinicalPaperSheet, PrintPage, PrintToolbar } from "./clinical-print-frame";
import { paperTraceability } from "./clinical-print-traceability";

export {
  ClinicalPaperSheet,
  PaperTraceability,
  PrintFooter,
  PrintHeader,
  PrintPage,
  PrintToolbar,
} from "./clinical-print-frame";

export function PrintPatientPage({ kind }: { kind: "ficha" | "resumen" | "receta" }) {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const record =
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) : null) ??
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
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) : null) ??
    recordQuery.data;
  const entry = record?.recent_entries.find((item) => item.id === entryId);

  return (
    <PrintPage>
      <PrintToolbar />
      {record && entry ? (
        <SoapPrintSheet record={record} entry={entry} />
      ) : (
        <p className="p-6 text-sm">
          {record ? "Evolucion no encontrada." : "Cargando evolucion..."}
        </p>
      )}
    </PrintPage>
  );
}

export function PatientSummaryPrintSheet({
  record,
  title,
}: {
  record: PatientRecordSnapshot;
  title: string;
}) {
  const isSummary = title === "Resumen";

  return (
    <ClinicalPaperSheet
      record={record}
      title={title}
      traceability={paperTraceability({
        source: "Snapshot de ficha paciente",
        status: isSummary ? "Resumen no persistido" : "Proyeccion longitudinal",
        actor: "No aplica",
        clinicalDate: "No aplica",
        limitation: isSummary
          ? "No reemplaza evolucion, epicrisis ni documento firmado."
          : "Proyeccion de lectura; no equivale a documento clinico firmado.",
      })}
    >
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

export function SoapPrintSheet({
  record,
  entry,
}: {
  record: PatientRecordSnapshot;
  entry: ClinicalEntry;
}) {
  return (
    <ClinicalPaperSheet
      record={record}
      title="Evolucion SOAP"
      traceability={paperTraceability({
        source: `clinical_entries/${entry.id}`,
        status: formatClinicalEntryStatus(entry.status),
        actor: entry.created_by,
        clinicalDate: formatDateTime(entry.occurred_at),
        limitation: "Sin firma legal; el registro directo por ID se mantiene para trazabilidad.",
      })}
    >
      <section className="print-section space-y-3">
        <div>
          <h2 className="text-sm font-semibold">{entry.title}</h2>
          <p className="text-xs text-muted-foreground">
            {formatDateTime(entry.occurred_at)} - Estado: {formatClinicalEntryStatus(entry.status)}
          </p>
        </div>
        <SoapRow label="S" value={entry.subjective} />
        <SoapRow label="O" value={entry.objective} />
        <SoapRow label="A" value={entry.assessment} />
        <SoapRow label="P" value={entry.plan} />
      </section>
    </ClinicalPaperSheet>
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
