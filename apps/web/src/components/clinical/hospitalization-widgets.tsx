import Link from "next/link";

import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { HospitalizationBoardItem } from "@/lib/types";

import { formatDateTime } from "./date-format";

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

export function RoundList() {
  return <EmptyState title="Rondas" description="Vista reservada para trabajo hospitalizado diario." />;
}

function formatHospitalBed(item: HospitalizationBoardItem) {
  if (item.bed) {
    return `${item.bed.ward} / ${item.bed.room} / Cama ${item.bed.bed_label}`;
  }
  return item.encounter.location_label ?? "Ubicacion pendiente";
}
