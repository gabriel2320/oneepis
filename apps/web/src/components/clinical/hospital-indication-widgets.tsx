"use client";

import Link from "next/link";
import { FileText, Lock, Printer, Save } from "lucide-react";

import { FreeTextClinicalEditor, PaperLikePanel } from "@/components/clinical/clinical-workspace";
import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { HospitalIndication, HospitalIndicationCreate, HospitalIndicationStatus } from "@/lib/types";

import { formatDateTime } from "./date-format";
import { Field, emptyToNull } from "./patient-page-shared";

export type HospitalIndicationFormState = {
  indicated_at: string;
  title: string;
  indication_text: string;
  rationale: string;
  safety_notes: string;
};

export const emptyHospitalIndicationForm = (): HospitalIndicationFormState => ({
  indicated_at: new Date().toISOString().slice(0, 16),
  title: "",
  indication_text: "",
  rationale: "",
  safety_notes: "Borrador no firmado. Requiere revision humana.",
});

export function HospitalIndicationForm({
  formState,
  setFormState,
  submitLabel,
  disabled,
  onSubmit,
}: {
  formState: HospitalIndicationFormState;
  setFormState: (value: HospitalIndicationFormState) => void;
  submitLabel: string;
  disabled: boolean;
  onSubmit: () => void;
}) {
  return (
    <PaperLikePanel
      title="Nueva indicacion hospitalaria"
      description="Borrador tipo papel; requiere cierre y revision humana."
    >
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <div className="grid gap-4 md:grid-cols-[180px_minmax(0,1fr)]">
          <Field label="Fecha y hora">
            <Input
              type="datetime-local"
              disabled={disabled}
              value={formState.indicated_at}
              onChange={(event) => setFormState({ ...formState, indicated_at: event.target.value })}
            />
          </Field>
          <Field label="Titulo">
            <Input
              disabled={disabled}
              value={formState.title}
              placeholder="Indicaciones medicas"
              onChange={(event) => setFormState({ ...formState, title: event.target.value })}
            />
          </Field>
        </div>
        <FreeTextClinicalEditor
          label="Indicaciones"
          value={formState.indication_text}
          disabled={disabled}
          minHeightClassName="min-h-[420px]"
          placeholder={"Dieta:\nReposo/actividad:\nControl signos vitales:\nMedicamentos:\nExamenes/controles:"}
          onChange={(value) => setFormState({ ...formState, indication_text: value })}
        />
        <details className="rounded-md border bg-muted/20 p-3">
          <summary className="cursor-pointer text-sm font-medium">Motivo y seguridad</summary>
          <div className="mt-4 grid gap-4">
            <Field label="Motivo">
              <Textarea
                disabled={disabled}
                value={formState.rationale}
                onChange={(event) => setFormState({ ...formState, rationale: event.target.value })}
              />
            </Field>
            <Field label="Seguridad">
              <Textarea
                disabled={disabled}
                value={formState.safety_notes}
                onChange={(event) => setFormState({ ...formState, safety_notes: event.target.value })}
              />
            </Field>
          </div>
        </details>
        <Button
          type="submit"
          disabled={
            disabled ||
            !formState.indicated_at ||
            !formState.title.trim() ||
            !formState.indication_text.trim()
          }
        >
          <Save className="h-4 w-4" />
          {submitLabel}
        </Button>
      </form>
    </PaperLikePanel>
  );
}

export function HospitalIndicationList({
  indications,
  patientId,
  canWrite,
  closingId,
  onClose,
}: {
  indications: HospitalIndication[];
  patientId: string;
  canWrite: boolean;
  closingId?: string | null;
  onClose: (indication: HospitalIndication) => void;
}) {
  if (indications.length === 0) {
    return (
      <EmptyState
        title="Sin indicaciones"
        description="Aun no hay borradores de indicacion para este ingreso hospitalario."
      />
    );
  }

  return (
    <div className="space-y-3">
      {indications.map((indication) => (
        <article key={indication.id} className="rounded-md border p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-sm font-semibold">{indication.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(indication.indicated_at)} - {indication.created_by}
              </p>
              <Badge
                className="mt-2"
                variant={indication.status === "closed" ? "safe" : "outline"}
              >
                {hospitalIndicationStatusLabel[indication.status]}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              {indication.status === "draft" ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!canWrite || closingId === indication.id}
                  onClick={() => onClose(indication)}
                >
                  <Lock className="h-4 w-4" />
                  {closingId === indication.id ? "Cerrando..." : "Cerrar borrador"}
                </Button>
              ) : null}
              <Button asChild variant="outline" size="sm">
                <Link
                  href={`/print/hospitalizacion/pacientes/${patientId}/indicacion/${indication.id}`}
                >
                  <Printer className="h-4 w-4" />
                  Imprimir
                </Link>
              </Button>
            </div>
          </div>
          <IndicationText label="Indicacion" value={indication.indication_text} />
          <IndicationText label="Motivo" value={indication.rationale} />
          <IndicationText label="Seguridad" value={indication.safety_notes} />
          <p className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
            <FileText className="h-3.5 w-3.5" />
            Borrador hospitalario; no sustituye firma ni orden ejecutable.
          </p>
        </article>
      ))}
    </div>
  );
}

export function toHospitalIndicationPayload(
  formState: HospitalIndicationFormState,
): HospitalIndicationCreate {
  return {
    indicated_at: new Date(formState.indicated_at).toISOString(),
    title: formState.title,
    indication_text: formState.indication_text,
    rationale: emptyToNull(formState.rationale),
    safety_notes: emptyToNull(formState.safety_notes),
  };
}

export const hospitalIndicationStatusLabel: Record<HospitalIndicationStatus, string> = {
  draft: "Borrador",
  closed: "Cerrada",
};

function IndicationText({ label, value }: { label: string; value?: string | null }) {
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
