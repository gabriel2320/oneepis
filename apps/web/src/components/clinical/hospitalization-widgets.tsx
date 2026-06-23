import Link from "next/link";
import { ClipboardList, FileText, Printer } from "lucide-react";

import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { HospitalizationBoardItem } from "@/lib/types";

import { formatDateTime } from "./date-format";
import {
  formatBedLabel,
  useHospitalDailySheets,
  type HospitalizationBoardState,
} from "./hospitalization-data";
import { dailySheetStatusLabel } from "./hospital-daily-sheet-widgets";

export function BedBoard({ items = [] }: { items?: HospitalizationBoardItem[] }) {
  if (items.length === 0) {
    return <EmptyState title="Sin hospitalizaciones activas" description="No hay encuentros hospitalarios en curso." />;
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {items.map((item) => (
        <div key={item.encounter.id} className="rounded-md border p-3">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">
                {item.patient.first_name} {item.patient.last_name}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{formatHospitalBed(item)}</p>
            </div>
            <Badge variant="safe">{item.bed?.status ?? item.encounter.status}</Badge>
          </div>
          <p className="mt-3 text-sm">{item.encounter.reason}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Ingreso: {formatDateTime(item.encounter.started_at)}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button asChild variant="outline" size="sm">
              <Link href={`/pacientes/${item.patient.id}/ficha`}>Ficha</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href={`/hospitalizacion/pacientes/${item.patient.id}/ingreso`}>
                Ingreso medico
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href={`/hospitalizacion/pacientes/${item.patient.id}/hoja-diaria`}>
                Hoja diaria
              </Link>
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function RoundList({ board }: { board: HospitalizationBoardState }) {
  if (board.isLoading) {
    return <LoadingRows rows={3} />;
  }
  if (board.isError) {
    return <ErrorState description="No se pudo cargar la ronda hospitalaria." onRetry={board.refetch} />;
  }
  if (board.items.length === 0) {
    return <EmptyState title="Sin pacientes en ronda" description="No hay ingresos hospitalarios activos." />;
  }

  return (
    <div className="space-y-3">
      {board.items.map((item) => (
        <HospitalRoundItem key={item.encounter.id} item={item} />
      ))}
    </div>
  );
}

function HospitalRoundItem({ item }: { item: HospitalizationBoardItem }) {
  const dailySheets = useHospitalDailySheets(item.patient.id);
  const latestDailySheet = dailySheets.items.find(
    (sheet) => sheet.encounter_id === item.encounter.id,
  );
  const bedLabel = item.bed ? formatBedLabel(item.bed) : item.encounter.location_label;

  return (
    <article className="rounded-md border p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold">
              {item.patient.first_name} {item.patient.last_name}
            </p>
            <Badge variant={item.bed ? "safe" : "outline"}>
              {item.bed ? "Con cama" : "Cama pendiente"}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {bedLabel ?? "Ubicacion pendiente"} - {item.encounter.reason}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Ingreso: {formatDateTime(item.encounter.started_at)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" size="sm">
            <Link href={`/pacientes/${item.patient.id}/ficha`}>
              <FileText className="h-4 w-4" />
              Ficha
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href={`/hospitalizacion/pacientes/${item.patient.id}/ingreso`}>
              <FileText className="h-4 w-4" />
              Ingreso
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href={`/hospitalizacion/pacientes/${item.patient.id}/hoja-diaria`}>
              <ClipboardList className="h-4 w-4" />
              Hoja diaria
            </Link>
          </Button>
          {latestDailySheet ? (
            <Button asChild variant="outline" size="sm">
              <Link
                href={`/print/hospitalizacion/pacientes/${item.patient.id}/hoja-diaria/${latestDailySheet.id}`}
              >
                <Printer className="h-4 w-4" />
                Imprimir
              </Link>
            </Button>
          ) : null}
        </div>
      </div>

      <div className="mt-4 rounded-md bg-muted/40 p-3">
        {dailySheets.isLoading ? <LoadingRows rows={1} /> : null}
        {dailySheets.isError ? (
          <ErrorState description="No se pudo cargar la hoja diaria." onRetry={dailySheets.refetch} />
        ) : null}
        {!dailySheets.isLoading && !dailySheets.isError && latestDailySheet ? (
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-xs font-semibold uppercase text-muted-foreground">
                Ultima hoja diaria {latestDailySheet.sheet_date}
              </p>
              <Badge variant={latestDailySheet.status === "closed" ? "safe" : "outline"}>
                {dailySheetStatusLabel[latestDailySheet.status]}
              </Badge>
            </div>
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
        ) : null}
        {!dailySheets.isLoading && !dailySheets.isError && !latestDailySheet ? (
          <EmptyState
            title="Sin hoja diaria para este ingreso"
            description="La ronda puede continuar leyendo ficha y cama, pero falta el registro diario."
          />
        ) : null}
      </div>
    </article>
  );
}

function formatHospitalBed(item: HospitalizationBoardItem) {
  if (item.bed) {
    return `${item.bed.ward} / ${item.bed.room} / Cama ${item.bed.bed_label}`;
  }
  return item.encounter.location_label ?? "Ubicacion pendiente";
}
