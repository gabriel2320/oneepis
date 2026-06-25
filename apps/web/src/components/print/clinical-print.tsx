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
import {
  ClinicalPaperSheet,
  PrintFooter,
  PrintHeader,
  PrintPage,
  PrintTextBlock,
  PrintToolbar,
} from "./paper-primitives";

export {
  ClinicalPaperSheet,
  PrintFooter,
  PrintHeader,
  PrintPage,
  PrintTextBlock,
  PrintToolbar,
} from "./paper-primitives";

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
          {record ? "Hoja diaria no encontrada." : "Cargando hoja diaria..."}
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
    <ClinicalPaperSheet record={record} title={title}>
      <PrintSourceSummary record={record} title={title} />
      <section className="print-section">
        <h2 className="text-sm font-semibold">Identificacion</h2>
        <div className="mt-2 grid gap-2 text-sm md:grid-cols-2">
          <p>
            <span className="font-medium">Nombre:</span> {record.patient.first_name}{" "}
            {record.patient.last_name}
          </p>
          <p>
            <span className="font-medium">Nacimiento:</span> {record.patient.birth_date}
          </p>
          <p>
            <span className="font-medium">Sexo registrado:</span> {record.patient.sex_at_birth}
          </p>
          <p>
            <span className="font-medium">Identificador clinico:</span>{" "}
            {record.patient.clinical_identifier ?? "sin identificador"}
          </p>
          <p>
            <span className="font-medium">Estado ficha:</span> {record.patient.clinical_status}
          </p>
          <p>
            <span className="font-medium">Contexto:</span> {record.patient.current_care_context}
          </p>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">Fuente: patients</p>
      </section>
      <PrintStructuredAntecedents record={record} />
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

function PrintStructuredAntecedents({ record }: { record: PatientRecordSnapshot }) {
  return (
    <section className="print-section">
      <h2 className="text-sm font-semibold">Antecedentes estructurados</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <PrintAntecedentColumn
          title="Problemas activos"
          source="active_problem"
          emptyLabel="Sin problemas activos"
          items={record.active_problems.map((problem) => ({
            id: problem.id,
            title: problem.title,
            detail: [problem.code_system, problem.code].filter(Boolean).join(" ") || "Sin codigo",
            meta: `Inicio: ${problem.onset_date ?? "sin fecha"}`,
          }))}
        />
        <PrintAntecedentColumn
          title="Alergias activas"
          source="allergy"
          emptyLabel="Sin alergias activas"
          items={record.active_allergies.map((allergy) => ({
            id: allergy.id,
            title: allergy.substance,
            detail: allergy.reaction ?? "Reaccion no documentada",
            meta: `Severidad: ${allergy.severity}`,
          }))}
        />
        <PrintAntecedentColumn
          title="Medicacion activa"
          source="medication"
          emptyLabel="Sin medicacion activa"
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
      <p className="mt-2 text-xs text-muted-foreground">
        Este bloque imprime las fuentes estructuradas existentes; no crea antecedentes nuevos.
      </p>
    </section>
  );
}

function PrintAntecedentColumn({
  title,
  source,
  emptyLabel,
  items,
}: {
  title: string;
  source: string;
  emptyLabel: string;
  items: { id: string; title: string; detail: string; meta: string }[];
}) {
  return (
    <div className="rounded-md border p-3">
      <h3 className="text-xs font-semibold uppercase text-muted-foreground">{title}</h3>
      <p className="mt-1 text-[11px] text-muted-foreground">Fuente: {source}</p>
      {items.length > 0 ? (
        <ul className="mt-2 space-y-2">
          {items.slice(0, 4).map((item) => (
            <li key={item.id} className="text-xs">
              <p className="font-medium text-foreground">{item.title}</p>
              <p className="text-muted-foreground">{item.detail}</p>
              <p className="text-muted-foreground">{item.meta}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-xs text-muted-foreground">{emptyLabel}</p>
      )}
    </div>
  );
}

function PrintSourceSummary({
  record,
  title,
}: {
  record: PatientRecordSnapshot;
  title: string;
}) {
  return (
    <section className="print-section rounded-md border border-info/30 bg-info/10 p-3">
      <h2 className="text-sm font-semibold">Estado y fuentes</h2>
      <div className="mt-2 grid gap-2 text-xs text-muted-foreground md:grid-cols-2">
        <p>Documento: {title}</p>
        <p>Estado ficha: {record.patient.clinical_status}</p>
        <p>Paciente: {record.patient.id}</p>
        <p>Contexto: {record.patient.current_care_context}</p>
        <p>Evoluciones: {record.recent_entries.length}</p>
        <p>Signos vitales recientes: {record.latest_vitals ? record.latest_vitals.id : "sin dato"}</p>
        <p>Alergias activas: {record.active_allergies.length}</p>
        <p>Medicacion activa: {record.active_medications.length}</p>
        <p>Problemas activos: {record.active_problems.length}</p>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Este papel proyecta datos existentes de ficha; no crea ni corrige datos clinicos.
      </p>
    </section>
  );
}

export function PrescriptionA5Sheet({ record }: { record: PatientRecordSnapshot }) {
  return (
    <article className="print-sheet mx-auto min-h-[210mm] max-w-[148mm] border-2 border-warning bg-card p-6 shadow-sm">
      <PrintHeader record={record} title="Receta bloqueada" />
      <div className="space-y-5 py-6">
        <section className="print-section rounded-md border-2 border-warning bg-warning/10 p-4">
          <h2 className="text-sm font-semibold uppercase text-warning-foreground">
            No emitir como receta clinica
          </h2>
          <p className="mt-2 text-sm font-medium">
            Documento bloqueado: no valido para prescribir, dispensar, indicar tratamiento ni
            respaldar compra de medicamentos.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            La prescripcion requiere autenticacion, permisos, validacion clinica, firma profesional
            y politica institucional habilitada.
          </p>
        </section>
        <section className="print-section">
          <h2 className="text-sm font-semibold">Referencia de paciente</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {record.patient.clinical_identifier ?? record.patient.id}
          </p>
        </section>
        <section className="print-section rounded-md border border-warning/40 bg-warning/10 p-4">
          <h2 className="text-sm font-semibold">Requisitos pendientes</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            <li>firma profesional gobernada</li>
            <li>folio o identificador documental inmutable</li>
            <li>actor profesional visible y validado</li>
            <li>fecha clinica de emision</li>
            <li>permisos de prescripcion definidos</li>
            <li>modelo/API de receta con auditoria y OpenAPI</li>
          </ul>
        </section>
        <section className="print-section min-h-32 border-t pt-4">
          <p className="text-sm font-semibold uppercase">Sin medicamentos autorizados</p>
          <p className="mt-2 text-sm text-muted-foreground">
            OneEpis no imprime recetas mientras el modulo de prescripcion permanezca bloqueado.
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
  const statusLabel = {
    amended: "Enmendada",
    draft: "Borrador no firmado",
    signed: "Firmada en estado clinico; sin firma legal digital",
  }[entry.status];

  return (
    <ClinicalPaperSheet record={record} title="Evolucion SOAP">
      <section className="print-section rounded-md border border-info/30 bg-info/10 p-3">
        <h2 className="text-sm font-semibold">Estado documental</h2>
        <div className="mt-2 grid gap-2 text-xs text-muted-foreground md:grid-cols-2">
          <p>Estado: {statusLabel}</p>
          <p>Entrada: {entry.id}</p>
          <p>Paciente: {entry.patient_id}</p>
          <p>Identificador clinico: {record.patient.clinical_identifier ?? "sin identificador"}</p>
          <p>Contexto: {record.patient.current_care_context}</p>
          <p>Encuentro: {entry.encounter_id ?? "Sin encuentro vinculado"}</p>
          <p>Autor registrado: {entry.created_by}</p>
          <p>Actualizada: {formatDateTime(entry.updated_at)}</p>
          <p>Fuente: clinical_entries</p>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Este papel proyecta una evolucion existente; no crea una nueva verdad clinica.
        </p>
      </section>
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
      <section className="print-section rounded-md border border-warning/40 bg-warning/10 p-3">
        <h2 className="text-sm font-semibold">Estado documental</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {sheet.status === "closed"
            ? "Cerrada bloquea edicion posterior para trazabilidad; no equivale a firma legal."
            : "Borrador editable; no firmado ni ejecutable como documento legal."}
        </p>
      </section>
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
