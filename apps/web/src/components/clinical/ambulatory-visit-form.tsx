"use client";

import { CheckCircle2, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import { Field } from "./patient-page-shared";

export type AmbulatoryVisitFormState = {
  started_at: string;
  reason: string;
  location_label: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

export type AmbulatoryVisitSaveFeedback =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "saved"; title: string }
  | { kind: "error"; message: string };

export function AmbulatoryVisitForm({
  formState,
  setFormState,
  disabled,
  submitLabel,
  onSubmit,
  feedback = { kind: "idle" },
}: {
  formState: AmbulatoryVisitFormState;
  setFormState: (value: AmbulatoryVisitFormState) => void;
  disabled: boolean;
  submitLabel: string;
  onSubmit: () => void;
  feedback?: AmbulatoryVisitSaveFeedback;
}) {
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <Field label="Fecha y hora">
        <Input
          type="datetime-local"
          disabled={disabled}
          value={formState.started_at}
          onChange={(event) => setFormState({ ...formState, started_at: event.target.value })}
        />
      </Field>
      <Field label="Motivo">
        <Input
          disabled={disabled}
          value={formState.reason}
          onChange={(event) => setFormState({ ...formState, reason: event.target.value })}
        />
      </Field>
      <Field label="Lugar">
        <Input
          disabled={disabled}
          value={formState.location_label}
          onChange={(event) =>
            setFormState({ ...formState, location_label: event.target.value })
          }
        />
      </Field>
      <Field label="Nota clinica libre">
        <Textarea
          className="min-h-48 leading-6"
          placeholder="Escribe la atencion en lenguaje clinico libre."
          disabled={disabled}
          value={formState.subjective}
          onChange={(event) => setFormState({ ...formState, subjective: event.target.value })}
        />
      </Field>
      <details className="rounded-md border bg-muted/20 p-3">
        <summary className="cursor-pointer text-sm font-medium text-foreground">
          SOAP detallado (opcional)
        </summary>
        <div className="mt-3 space-y-4">
          <SoapField
            label="Objetivo"
            value={formState.objective}
            disabled={disabled}
            onChange={(value) => setFormState({ ...formState, objective: value })}
          />
          <SoapField
            label="Analisis"
            value={formState.assessment}
            disabled={disabled}
            onChange={(value) => setFormState({ ...formState, assessment: value })}
          />
          <SoapField
            label="Plan"
            value={formState.plan}
            disabled={disabled}
            onChange={(value) => setFormState({ ...formState, plan: value })}
          />
        </div>
      </details>
      <div className="space-y-2">
        <Button
          type="submit"
          disabled={disabled || !formState.started_at || !formState.reason.trim()}
        >
          <Save className="h-4 w-4" />
          {submitLabel}
        </Button>
        <SaveFeedbackLine feedback={feedback} />
      </div>
    </form>
  );
}

function SaveFeedbackLine({ feedback }: { feedback: AmbulatoryVisitSaveFeedback }) {
  if (feedback.kind === "saving") {
    return <p className="text-sm text-muted-foreground">Guardando borrador...</p>;
  }
  if (feedback.kind === "saved") {
    return (
      <p className="flex items-center gap-1.5 text-sm font-medium text-foreground">
        <CheckCircle2 className="h-4 w-4 text-primary" />
        Guardado como borrador clinico: {feedback.title}
      </p>
    );
  }
  if (feedback.kind === "error") {
    return <p className="text-sm text-destructive">{feedback.message}</p>;
  }
  return (
    <p className="text-xs text-muted-foreground">
      Al guardar, la atencion queda como borrador clinico; no firma ni emite documento.
    </p>
  );
}

function SoapField({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <Field label={label}>
      <Textarea
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </Field>
  );
}
