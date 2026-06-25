"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { formatDateTime } from "@/components/clinical/date-format";
import {
  ClinicalPaperSheet,
  PrintPage,
  PrintToolbar,
} from "@/components/print/clinical-print";
import { getClinicalEntry } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { getPatientRecord } from "@/lib/api/patients";
import { demoRecords } from "@/lib/demo-record";
import type { ClinicalEntry, PatientRecordSnapshot } from "@/lib/types";

export function PrintHospitalDischargeSummaryPage() {
  const params = useParams<{ patientId: string; entryId: string }>();
  const patientId = params.patientId;
  const entryId = params.entryId;
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const entryQuery = useQuery({
    queryKey: ["clinical-entry", patientId, entryId],
    queryFn: () => getClinicalEntry(patientId, entryId),
    enabled: Boolean(patientId && entryId) && !DEMO_MODE,
  });
  const record =
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) : null) ??
    recordQuery.data;
  const entry =
    (DEMO_MODE ? record?.recent_entries.find((item) => item.id === entryId) : null) ??
    entryQuery.data;
  const dischargeSummary = entry?.kind === "discharge_summary" ? entry : null;

  return (
    <PrintPage>
      <PrintToolbar />
      {record && dischargeSummary ? (
        <HospitalDischargeSummaryPrintSheet record={record} entry={dischargeSummary} />
      ) : (
        <p className="p-6 text-sm">
          {record ? "Epicrisis no encontrada." : "Cargando epicrisis..."}
        </p>
      )}
    </PrintPage>
  );
}

function HospitalDischargeSummaryPrintSheet({
  record,
  entry,
}: {
  record: PatientRecordSnapshot;
  entry: ClinicalEntry;
}) {
  return (
    <ClinicalPaperSheet
      record={record}
      title="Alta y epicrisis"
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
          <p className="text-xs text-muted-foreground">
            {formatDateTime(entry.occurred_at)} - Estado:{" "}
            {entry.status === "draft" ? "Borrador" : entry.status}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Registrado por {entry.created_by}
          </p>
        </div>
        <PrintTextBlock label="Motivo de ingreso y antecedentes" value={entry.subjective} />
        <PrintTextBlock label="Evolucion intrahospitalaria" value={entry.objective} />
        <PrintTextBlock label="Diagnosticos de egreso" value={entry.assessment} />
        <PrintTextBlock label="Plan de alta y seguimiento" value={entry.plan} />
      </section>
    </ClinicalPaperSheet>
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
