"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { formatDateTime } from "@/components/clinical/date-format";
import { ClinicalTimeline } from "@/components/clinical/patient-widgets";
import { DEMO_MODE } from "@/lib/api/client";
import { listHospitalDailySheets } from "@/lib/api/hospitalization";
import { getPatientRecord } from "@/lib/api/patients";
import { demoHospitalDailySheets, demoRecords } from "@/lib/demo-record";
import type { ClinicalEntry, HospitalDailySheet, PatientRecordSnapshot } from "@/lib/types";

import { PrescriptionA5Sheet } from "./blocked-prescription-print";
import { ClinicalPaperSheet, PrintPage, PrintToolbar } from "./clinical-print-frame";

export {
  ClinicalPaperSheet,
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
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) : null) ??
    recordQuery.data;
  const sheets = DEMO_MODE
    ? demoHospitalDailySheets.filter((item) => item.patient_id === patientId)
    : (sheetsQuery.data ?? []);
  const sheet = sheets.find((item) => item.id === sheetId);

  return (
    <PrintPage>
      <PrintToolbar />
      {record && sheet ? (
        <HospitalDailyPrintSheet record={record} sheet={sheet} />
      ) : (
        <p className="p-6 text-sm">
          {record ? "Evolucion diaria no encontrada." : "Cargando evolucion diaria..."}
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
  return (
    <ClinicalPaperSheet
      record={record}
      title={title}
      metadata={{
        source: "record paciente",
        status: title === "Ficha clinica" ? "Ficha de lectura no firmada" : "Resumen no persistido",
      }}
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
        <h2 className="text-sm font-semibold">Diagnosticos historicos</h2>
        {record.historical_diagnoses.length ? (
          <ul className="mt-2 space-y-2 text-sm">
            {record.historical_diagnoses.map((diagnosis) => (
              <li key={diagnosis.source_event_id} className="rounded-md border p-2">
                <p className="font-medium">{diagnosis.title}</p>
                <p className="text-xs text-muted-foreground">
                  Fuente: {diagnosis.source_label}
                  {diagnosis.code ? ` / Codigo: ${diagnosis.code}` : ""}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">{diagnosis.limit}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm">Sin diagnosticos historicos curados</p>
        )}
      </section>
      <section className="print-section">
        <h2 className="mb-3 text-sm font-semibold">Evoluciones recientes</h2>
        <ClinicalTimeline entries={record.recent_entries} />
      </section>
      <section className="print-section rounded-md border border-info/30 bg-info/10 p-3">
        <h2 className="text-sm font-semibold">Resumen IA</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          No se imprime contenido IA persistido. Las sugerencias asistidas son borradores y no sustituyen
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
      metadata={{
        source: `clinical entry ${entry.id}`,
        status: entry.status === "draft" ? "Borrador no firmado" : entry.status,
        actor: entry.created_by,
        clinicalDate: formatDateTime(entry.occurred_at),
      }}
    >
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
    <ClinicalPaperSheet
      record={record}
      title="Evolucion diaria hospitalaria"
      metadata={{
        source: `evolucion diaria ${sheet.id}`,
        status: sheet.status === "closed" ? "Cerrada no firmada" : "Borrador no firmado",
        actor: sheet.created_by,
        clinicalDate: sheet.sheet_date,
      }}
    >
      <section className="print-section space-y-3">
        <div>
          <h2 className="text-sm font-semibold">Fecha {sheet.sheet_date}</h2>
          <p className="text-xs text-muted-foreground">
            Registrada por {sheet.created_by} - {formatDateTime(sheet.created_at)}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Estado: {sheet.status === "closed" ? "Cerrada" : "Borrador"}
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
