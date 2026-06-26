"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import {
  Bed,
  ClipboardCheck,
  ClipboardList,
  Stethoscope,
} from "lucide-react";

import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { HospitalizationBoardItem } from "@/lib/types";

import { formatDateTime } from "./date-format";
import { dailySheetStatusLabel } from "./hospital-daily-sheet-widgets";
import { hospitalIndicationStatusLabel } from "./hospital-indication-widgets";
import {
  formatBedLabel,
  useHospitalBeds,
  useHospitalDailySheets,
  useHospitalIndications,
  type HospitalizationBoardState,
} from "./hospitalization-data";

export function HospitalCommandCenter({ board }: { board: HospitalizationBoardState }) {
  const beds = useHospitalBeds();

  if (board.isLoading || beds.isLoading) {
    return <LoadingRows rows={4} />;
  }
  if (board.isError) {
    return <ErrorState description="No se pudo cargar el tablero hospitalario." onRetry={board.refetch} />;
  }
  if (beds.isError) {
    return <ErrorState description="No se pudo cargar el resumen de camas." onRetry={beds.refetch} />;
  }

  const activeCount = board.items.length;
  const withoutBedCount = board.items.filter((item) => !item.bed).length;
  const occupiedCount = beds.items.filter((bed) => bed.status === "occupied").length;
  const availableCount = beds.items.filter((bed) => bed.status === "available").length;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <HospitalMetric
          icon={<Stethoscope className="h-4 w-4" />}
          label="Ingresos activos"
          value={String(activeCount)}
        />
        <HospitalMetric
          icon={<Bed className="h-4 w-4" />}
          label="Sin cama"
          value={String(withoutBedCount)}
          tone={withoutBedCount > 0 ? "warning" : "safe"}
        />
        <HospitalMetric
          icon={<ClipboardList className="h-4 w-4" />}
          label="Evolucion diaria"
          value="Revisar hoy"
        />
        <HospitalMetric
          icon={<ClipboardCheck className="h-4 w-4" />}
          label="Camas disponibles"
          value={String(availableCount)}
          detail={`${occupiedCount} ocupadas`}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="rounded-md border bg-card">
          <div className="border-b p-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-base font-semibold">Trabajo hospitalario de hoy</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Pacientes activos con ubicacion, estado diario y siguiente accion.
                </p>
              </div>
              <Button asChild variant="outline" size="sm">
                <Link href="/hospitalizacion/rondas">Ver evolucion completa</Link>
              </Button>
            </div>
          </div>
          <HospitalWorklist items={board.items} />
        </section>

        <aside className="space-y-4">
          <section className="rounded-md border bg-card p-4">
            <h2 className="text-base font-semibold">Camas</h2>
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <BedSummaryItem label="Disponibles" value={availableCount} />
              <BedSummaryItem label="Ocupadas" value={occupiedCount} />
              <BedSummaryItem
                label="Limpieza"
                value={beds.items.filter((bed) => bed.status === "cleaning").length}
              />
              <BedSummaryItem
                label="Bloqueadas"
                value={beds.items.filter((bed) => bed.status === "blocked").length}
              />
            </div>
            <Button asChild className="mt-4 w-full" variant="outline" size="sm">
              <Link href="/hospitalizacion/camas">Administrar camas</Link>
            </Button>
          </section>

          <section className="rounded-md border bg-card p-4">
            <h2 className="text-base font-semibold">Flujo clinico</h2>
            <div className="mt-3 grid gap-2">
              <QuickLink href="/hospitalizacion/camas" label="Ingreso y cama" />
              <QuickLink href="/hospitalizacion/rondas" label="Evolucion diaria" />
              <QuickLink href="/print/hospitalizacion/rondas" label="Imprimir listado" />
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function HospitalMetric({
  icon,
  label,
  value,
  detail,
  tone = "outline",
}: {
  icon: ReactNode;
  label: string;
  value: string;
  detail?: string;
  tone?: "outline" | "warning" | "safe";
}) {
  return (
    <div className="rounded-md border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <Badge variant={tone}>{icon}</Badge>
      </div>
      <p className="mt-3 text-2xl font-semibold">{value}</p>
      {detail ? <p className="mt-1 text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}

function HospitalWorklist({ items }: { items: HospitalizationBoardItem[] }) {
  if (items.length === 0) {
    return <EmptyState title="Sin pacientes hospitalizados" description="No hay ingresos hospitalarios activos." />;
  }

  return (
    <div className="divide-y">
      {items.map((item) => (
        <HospitalWorklistRow key={item.encounter.id} item={item} />
      ))}
    </div>
  );
}

function HospitalWorklistRow({ item }: { item: HospitalizationBoardItem }) {
  const dailySheets = useHospitalDailySheets(item.patient.id);
  const indications = useHospitalIndications(item.patient.id);
  const latestDailySheet = dailySheets.items.find(
    (sheet) => sheet.encounter_id === item.encounter.id,
  );
  const latestIndication = indications.items[0];
  const draftIndications = indications.items.filter((indication) => indication.status === "draft").length;
  const bedLabel = item.bed ? formatBedLabel(item.bed) : item.encounter.location_label;
  const primaryAction = getHospitalPrimaryAction({
    item,
    hasDailySheet: Boolean(latestDailySheet),
    draftIndications,
  });

  return (
    <article className="grid gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_220px] lg:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold">
            {item.patient.first_name} {item.patient.last_name}
          </h3>
          <Badge variant={item.bed ? "safe" : "warning"}>
            {item.bed ? "Con cama" : "Cama pendiente"}
          </Badge>
          {latestDailySheet ? (
            <Badge variant={latestDailySheet.status === "closed" ? "safe" : "outline"}>
              {dailySheetStatusLabel[latestDailySheet.status]}
            </Badge>
          ) : (
            <Badge variant="warning">Sin evolucion hoy</Badge>
          )}
        </div>
        <p className="mt-1 truncate text-sm text-muted-foreground">
          {bedLabel ?? "Ubicacion pendiente"} - {item.encounter.reason}
        </p>
        <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
          <CompactClinicalDatum label="Ingreso" value={formatDateTime(item.encounter.started_at)} />
          <CompactClinicalDatum
            label="Evolucion"
            value={latestDailySheet ? latestDailySheet.sheet_date : "Pendiente"}
          />
          <CompactClinicalDatum
            label="Indicaciones"
            value={
              indications.isLoading
                ? "Cargando"
                : latestIndication
                  ? `${hospitalIndicationStatusLabel[latestIndication.status]}${draftIndications > 1 ? ` +${draftIndications - 1}` : ""}`
                  : "Sin registro"
            }
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2 lg:justify-end">
        <Button asChild size="sm">
          <Link href={primaryAction.href}>{primaryAction.label}</Link>
        </Button>
        <Button asChild variant="outline" size="sm">
          <Link href={`/hospitalizacion/pacientes/${item.patient.id}/hoja-diaria`}>
            <ClipboardList className="h-4 w-4" />
            Evolucion
          </Link>
        </Button>
        <Button asChild variant="outline" size="sm">
          <Link href={`/hospitalizacion/pacientes/${item.patient.id}/indicaciones`}>
            <ClipboardCheck className="h-4 w-4" />
            Indicaciones
          </Link>
        </Button>
      </div>
    </article>
  );
}

function CompactClinicalDatum({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="font-medium text-foreground">{label}</p>
      <p className="mt-0.5 truncate">{value}</p>
    </div>
  );
}

function BedSummaryItem({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Button asChild variant="outline" size="sm" className="justify-start">
      <Link href={href}>{label}</Link>
    </Button>
  );
}

function getHospitalPrimaryAction({
  item,
  hasDailySheet,
  draftIndications,
}: {
  item: HospitalizationBoardItem;
  hasDailySheet: boolean;
  draftIndications: number;
}) {
  if (!item.bed) {
    return { href: "/hospitalizacion/camas", label: "Asignar cama" };
  }
  if (!hasDailySheet) {
    return {
      href: `/hospitalizacion/pacientes/${item.patient.id}/hoja-diaria`,
      label: "Evolucionar",
    };
  }
  if (draftIndications > 0) {
    return {
      href: `/hospitalizacion/pacientes/${item.patient.id}/indicaciones`,
      label: "Revisar indicaciones",
    };
  }
  return {
    href: `/hospitalizacion/pacientes/${item.patient.id}/epicrisis`,
    label: "Epicrisis",
  };
}
