"use client";

import { useQueries, useQuery } from "@tanstack/react-query";

import { formatDateTime } from "@/components/clinical/date-format";
import { formatBedLabel, getDemoHospitalizations } from "@/components/clinical/hospitalization-data";
import { DEMO_MODE } from "@/lib/api/client";
import { listActiveHospitalizations, listHospitalDailySheets } from "@/lib/api/hospitalization";
import { demoHospitalDailySheets } from "@/lib/demo-record";
import type { HospitalDailySheet, HospitalizationBoardItem } from "@/lib/types";

import { PaperTraceability, PrintFooter, PrintPage, PrintToolbar } from "./clinical-print";

type RoundPrintRow = {
  item: HospitalizationBoardItem;
  latestDailySheet: HospitalDailySheet | null;
};

export function PrintHospitalRoundPage() {
  const boardQuery = useQuery({
    queryKey: ["hospitalization-board"],
    queryFn: listActiveHospitalizations,
    enabled: !DEMO_MODE,
  });
  const board = DEMO_MODE ? getDemoHospitalizations() : (boardQuery.data ?? []);
  const dailySheetQueries = useQueries({
    queries: DEMO_MODE
      ? []
      : board.map((item) => ({
          queryKey: ["hospital-daily-sheets", item.patient.id],
          queryFn: () => listHospitalDailySheets(item.patient.id),
          enabled: Boolean(item.patient.id),
        })),
  });
  const isLoading = !DEMO_MODE && (boardQuery.isLoading || dailySheetQueries.some((item) => item.isLoading));
  const isError = !DEMO_MODE && (boardQuery.isError || dailySheetQueries.some((item) => item.isError));
  const rows: RoundPrintRow[] = board.map((item, index) => {
    const sheets = DEMO_MODE
      ? demoHospitalDailySheets.filter((sheet) => sheet.patient_id === item.patient.id)
      : (dailySheetQueries[index]?.data ?? []);
    return {
      item,
      latestDailySheet: getLatestDailySheetForEncounter(sheets, item.encounter.id),
    };
  });

  return (
    <PrintPage>
      <PrintToolbar />
      {isLoading ? <p className="p-6 text-sm">Cargando ronda hospitalaria...</p> : null}
      {isError ? <p className="p-6 text-sm">No se pudo cargar la ronda hospitalaria.</p> : null}
      {!isLoading && !isError ? <HospitalRoundPrintSheet rows={rows} /> : null}
    </PrintPage>
  );
}

function HospitalRoundPrintSheet({ rows }: { rows: RoundPrintRow[] }) {
  return (
    <article className="print-sheet mx-auto min-h-[279mm] max-w-4xl border bg-card p-8 shadow-sm print:min-h-[250mm]">
      <header className="border-b pb-4">
        <p className="text-xs font-semibold uppercase text-muted-foreground">OneEpis</p>
        <h1 className="mt-1 text-2xl font-semibold">Ronda hospitalaria</h1>
        <p className="mt-2 text-sm text-muted-foreground" suppressHydrationWarning>
          Fecha operacional: {new Date().toLocaleDateString("es-CL")}
        </p>
      </header>
      <PaperTraceability
        items={[
          { label: "Fuente", value: "hospitalization-board + hojas diarias" },
          { label: "Estado", value: "Lectura operacional" },
          { label: "Actor", value: "No aplica" },
          {
            label: "Fecha clinica",
            value: <span suppressHydrationWarning>{new Date().toLocaleDateString("es-CL")}</span>,
          },
        ]}
        limitation="Ronda de lectura; no reemplaza evolucion, indicacion ni hoja diaria firmada."
      />
      <div className="space-y-4 py-6">
        {rows.length === 0 ? (
          <section className="print-section rounded-md border border-dashed p-4">
            <h2 className="text-sm font-semibold">Sin pacientes en ronda</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              No hay ingresos hospitalarios activos para imprimir.
            </p>
          </section>
        ) : null}
        {rows.map((row) => (
          <HospitalRoundPrintRow key={row.item.encounter.id} row={row} />
        ))}
      </div>
      <PrintFooter />
    </article>
  );
}

function HospitalRoundPrintRow({ row }: { row: RoundPrintRow }) {
  const { item, latestDailySheet } = row;
  const bedLabel = item.bed ? formatBedLabel(item.bed) : item.encounter.location_label;

  return (
    <section className="print-section rounded-md border p-4">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(220px,280px)]">
        <div>
          <h2 className="text-sm font-semibold">
            {item.patient.first_name} {item.patient.last_name}
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.patient.clinical_identifier ?? item.patient.id}
          </p>
          <p className="mt-2 text-sm">{bedLabel ?? "Ubicacion pendiente"}</p>
          <p className="mt-1 text-sm text-muted-foreground">{item.encounter.reason}</p>
        </div>
        <div className="text-sm">
          <p className="text-xs font-semibold uppercase text-muted-foreground">Ingreso</p>
          <p className="mt-1">{formatDateTime(item.encounter.started_at)}</p>
          <p className="mt-3 text-xs font-semibold uppercase text-muted-foreground">Cama</p>
          <p className="mt-1">{item.bed ? "Asignada" : "Pendiente"}</p>
        </div>
      </div>
      {latestDailySheet ? (
        <div className="mt-4 border-t pt-3">
          <p className="text-xs font-semibold uppercase text-muted-foreground">
            Ultima hoja diaria {latestDailySheet.sheet_date} -{" "}
            {latestDailySheet.status === "closed" ? "Cerrada" : "Borrador"}
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm">{latestDailySheet.clinical_summary}</p>
          {latestDailySheet.pending_tasks ? (
            <p className="mt-2 text-sm text-muted-foreground">
              Pendientes: {latestDailySheet.pending_tasks}
            </p>
          ) : null}
          {latestDailySheet.safety_notes ? (
            <p className="mt-1 text-sm text-muted-foreground">
              Seguridad: {latestDailySheet.safety_notes}
            </p>
          ) : null}
        </div>
      ) : (
        <div className="mt-4 border-t pt-3">
          <p className="text-sm font-semibold">Sin hoja diaria para este ingreso</p>
          <p className="mt-1 text-sm text-muted-foreground">
            La ronda imprime cama e ingreso, pero falta registro diario.
          </p>
        </div>
      )}
    </section>
  );
}

function getLatestDailySheetForEncounter(
  sheets: HospitalDailySheet[],
  encounterId: string,
): HospitalDailySheet | null {
  return (
    sheets
      .filter((sheet) => sheet.encounter_id === encounterId)
      .sort(
        (left, right) =>
          right.sheet_date.localeCompare(left.sheet_date) ||
          right.created_at.localeCompare(left.created_at),
      )[0] ?? null
  );
}
