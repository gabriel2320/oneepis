"use client";

import Link from "next/link";
import { Plus } from "lucide-react";

import { EmptyState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import type { Medication, MedicationCatalogItem, MedicationDraftingContext } from "@/lib/types";

export function MedicationShortcutList({
  title,
  items,
  patientId,
  canWrite,
}: {
  title: string;
  items: MedicationCatalogItem[];
  patientId: string;
  canWrite: boolean;
}) {
  if (items.length === 0) {
    return <EmptyState title={`Sin ${title.toLowerCase()}`} description="No hay elementos." />;
  }
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-muted-foreground">{title}</p>
      {items.map((item) => (
        <div key={item.id} className="flex items-center justify-between gap-3 rounded-md border p-2">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{item.display_name}</p>
            <p className="truncate text-xs text-muted-foreground">{item.generic_name}</p>
          </div>
          <Button asChild size="sm" variant="outline" disabled={!canWrite}>
            <Link href={newMedicationHref(patientId, item)}>Usar</Link>
          </Button>
        </div>
      ))}
    </div>
  );
}

export function MedicationHistory({
  context,
  patientId,
  canWrite,
}: {
  context?: MedicationDraftingContext;
  patientId: string;
  canWrite: boolean;
}) {
  const medications = context?.recent_medications ?? [];
  if (medications.length === 0) {
    return <EmptyState title="Sin historial farmacologico" description="No hay medicacion previa." />;
  }
  return (
    <div className="space-y-2">
      {medications.slice(0, 5).map((medication) => (
        <div key={medication.id} className="flex items-center justify-between gap-3 rounded-md border p-2">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{medication.name}</p>
            <p className="truncate text-xs text-muted-foreground">
              {[medication.dose, medication.route, medication.frequency].filter(Boolean).join(" / ")}
            </p>
          </div>
          <Button asChild size="sm" variant="outline" disabled={!canWrite}>
            <Link href={medicationCopyHref(patientId, medication)}>Copiar</Link>
          </Button>
        </div>
      ))}
    </div>
  );
}

export function AddMedicationButton({
  item,
  patientId,
  canWrite,
}: {
  item: MedicationCatalogItem;
  patientId: string;
  canWrite: boolean;
}) {
  return (
    <Button asChild className="mt-3" size="sm" disabled={!canWrite}>
      <Link href={newMedicationHref(patientId, item)}>
        <Plus className="h-4 w-4" />
        Agregar
      </Link>
    </Button>
  );
}

export function newMedicationHref(patientId: string, item: MedicationCatalogItem) {
  const params = new URLSearchParams({
    catalogItemId: item.id,
    name: item.display_name,
  });
  if (item.route) {
    params.set("route", item.route);
  }
  return `/pacientes/${patientId}/medicacion/nueva?${params.toString()}`;
}

function medicationCopyHref(patientId: string, medication: Medication) {
  const params = new URLSearchParams({
    name: medication.name,
  });
  if (medication.catalog_item_id) params.set("catalogItemId", medication.catalog_item_id);
  if (medication.dose) params.set("dose", medication.dose);
  if (medication.route) params.set("route", medication.route);
  if (medication.frequency) params.set("frequency", medication.frequency);
  return `/pacientes/${patientId}/medicacion/nueva?${params.toString()}`;
}
