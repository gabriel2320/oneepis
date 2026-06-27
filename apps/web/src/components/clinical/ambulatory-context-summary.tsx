import type { ReactNode } from "react";

import { careContextLabel, clinicalStatusLabel } from "@/lib/patient-display";
import type { PatientRecordSnapshot, VitalSign } from "@/lib/types";

import { formatDateTime } from "./date-format";

export function AmbulatoryContextSummary({ record }: { record: PatientRecordSnapshot }) {
  const lastEntry = record.recent_entries[0] ?? null;
  const allergies = record.active_allergies;
  return (
    <dl className="space-y-2">
      <ContextRow label="Estado">
        {clinicalStatusLabel(record.patient.clinical_status)} ·{" "}
        {careContextLabel(record.patient.current_care_context)}
      </ContextRow>
      <ContextRow label="Alergias activas">
        {allergies.length === 0
          ? "Sin alergias activas"
          : allergies
              .map((item) => (item.severity === "severe" ? `${item.substance} (grave)` : item.substance))
              .join(", ")}
      </ContextRow>
      <ContextRow label="Problemas activos">
        {record.active_problems.length === 0
          ? "Sin antecedentes activos"
          : record.active_problems.map((item) => item.title).join(", ")}
      </ContextRow>
      <ContextRow label="Medicacion activa">
        {record.active_medications.length === 0
          ? "Sin medicacion activa"
          : record.active_medications.map((item) => item.name).join(", ")}
      </ContextRow>
      <ContextRow label="Ultima evolucion">
        {lastEntry ? `${lastEntry.title} · ${formatDateTime(lastEntry.occurred_at)}` : "Sin evoluciones"}
      </ContextRow>
      <ContextRow label="Ultimos signos">{formatVitalsLine(record.latest_vitals)}</ContextRow>
    </dl>
  );
}

function ContextRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b pb-2 last:border-0 last:pb-0 sm:flex-row sm:gap-3">
      <dt className="w-36 shrink-0 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </dt>
      <dd className="text-sm text-foreground">{children}</dd>
    </div>
  );
}

function formatVitalsLine(vital?: VitalSign | null) {
  if (!vital) {
    return "Sin signos recientes";
  }
  const parts: string[] = [];
  if (vital.systolic_bp && vital.diastolic_bp) {
    parts.push(`PA ${vital.systolic_bp}/${vital.diastolic_bp}`);
  }
  if (vital.heart_rate_bpm) {
    parts.push(`FC ${vital.heart_rate_bpm}`);
  }
  if (vital.oxygen_saturation_pct) {
    parts.push(`SatO2 ${vital.oxygen_saturation_pct}%`);
  }
  if (vital.temperature_c) {
    parts.push(`Temp ${vital.temperature_c} C`);
  }
  if (parts.length === 0) {
    return "Sin signos recientes";
  }
  return `${parts.join(" · ")} · ${formatDateTime(vital.measured_at)}`;
}
