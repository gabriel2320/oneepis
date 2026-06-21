"use client";

import Link from "next/link";
import { Pencil, Printer, Save } from "lucide-react";

import { EmptyState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { HospitalDailySheet, HospitalDailySheetCreate } from "@/lib/types";

import { formatDateTime } from "./date-format";
import { Field, emptyToNull } from "./patient-page-shared";

export type DailySheetFormState = {
  sheet_date: string;
  clinical_summary: string;
  overnight_events: string;
  active_plan: string;
  pending_tasks: string;
  safety_notes: string;
};

export const emptyDailySheetForm = (): DailySheetFormState => ({
  sheet_date: new Date().toISOString().slice(0, 10),
  clinical_summary: "",
  overnight_events: "",
  active_plan: "",
  pending_tasks: "",
  safety_notes: "",
});

export function DailySheetForm({
  formState,
  setFormState,
  submitLabel,
  disabled,
  onSubmit,
}: {
  formState: DailySheetFormState;
  setFormState: (value: DailySheetFormState) => void;
  submitLabel: string;
  disabled: boolean;
  onSubmit: () => void;
}) {
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <Field label="Fecha">
        <Input
          type="date"
          value={formState.sheet_date}
          onChange={(event) => setFormState({ ...formState, sheet_date: event.target.value })}
        />
      </Field>
      <Field label="Resumen clinico del dia">
        <Textarea
          className="min-h-28"
          value={formState.clinical_summary}
          onChange={(event) =>
            setFormState({ ...formState, clinical_summary: event.target.value })
          }
        />
      </Field>
      <Field label="Eventos relevantes">
        <Textarea
          value={formState.overnight_events}
          onChange={(event) =>
            setFormState({ ...formState, overnight_events: event.target.value })
          }
        />
      </Field>
      <Field label="Plan activo">
        <Textarea
          value={formState.active_plan}
          onChange={(event) => setFormState({ ...formState, active_plan: event.target.value })}
        />
      </Field>
      <Field label="Pendientes">
        <Textarea
          value={formState.pending_tasks}
          onChange={(event) => setFormState({ ...formState, pending_tasks: event.target.value })}
        />
      </Field>
      <Field label="Notas de seguridad">
        <Textarea
          value={formState.safety_notes}
          onChange={(event) => setFormState({ ...formState, safety_notes: event.target.value })}
        />
      </Field>
      <Button
        type="submit"
        disabled={disabled || !formState.sheet_date || !formState.clinical_summary.trim()}
      >
        <Save className="h-4 w-4" />
        {submitLabel}
      </Button>
    </form>
  );
}

export function DailySheetList({
  sheets,
  patientId,
}: {
  sheets: HospitalDailySheet[];
  patientId: string;
}) {
  if (sheets.length === 0) {
    return (
      <EmptyState
        title="Sin hojas diarias"
        description="Aun no hay registro diario para este ingreso hospitalario."
      />
    );
  }

  return (
    <div className="space-y-3">
      {sheets.map((sheet) => (
        <article key={sheet.id} className="rounded-md border p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-sm font-semibold">Hoja diaria {sheet.sheet_date}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Registrada por {sheet.created_by} - {formatDateTime(sheet.created_at)}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline" size="sm">
                <Link
                  href={`/hospitalizacion/pacientes/${patientId}/hoja-diaria/${sheet.id}/editar`}
                >
                  <Pencil className="h-4 w-4" />
                  Editar
                </Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link
                  href={`/print/hospitalizacion/pacientes/${patientId}/hoja-diaria/${sheet.id}`}
                >
                  <Printer className="h-4 w-4" />
                  Imprimir
                </Link>
              </Button>
            </div>
          </div>
          <DailySheetText label="Resumen" value={sheet.clinical_summary} />
          <DailySheetText label="Eventos" value={sheet.overnight_events} />
          <DailySheetText label="Plan" value={sheet.active_plan} />
          <DailySheetText label="Pendientes" value={sheet.pending_tasks} />
          <DailySheetText label="Seguridad" value={sheet.safety_notes} />
        </article>
      ))}
    </div>
  );
}

export function toDailySheetForm(sheet: HospitalDailySheet): DailySheetFormState {
  return {
    sheet_date: sheet.sheet_date,
    clinical_summary: sheet.clinical_summary,
    overnight_events: sheet.overnight_events ?? "",
    active_plan: sheet.active_plan ?? "",
    pending_tasks: sheet.pending_tasks ?? "",
    safety_notes: sheet.safety_notes ?? "",
  };
}

export function toDailySheetPayload(formState: DailySheetFormState): HospitalDailySheetCreate {
  return {
    sheet_date: formState.sheet_date,
    clinical_summary: formState.clinical_summary,
    overnight_events: emptyToNull(formState.overnight_events),
    active_plan: emptyToNull(formState.active_plan),
    pending_tasks: emptyToNull(formState.pending_tasks),
    safety_notes: emptyToNull(formState.safety_notes),
  };
}

function DailySheetText({ label, value }: { label: string; value?: string | null }) {
  if (!value) {
    return null;
  }
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-sm">{value}</p>
    </div>
  );
}
