"use client";

import { Save } from "lucide-react";

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

export function AmbulatoryVisitForm({
  formState,
  setFormState,
  disabled,
  submitLabel,
  onSubmit,
}: {
  formState: AmbulatoryVisitFormState;
  setFormState: (value: AmbulatoryVisitFormState) => void;
  disabled: boolean;
  submitLabel: string;
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
      <SoapField
        label="Subjetivo"
        value={formState.subjective}
        disabled={disabled}
        onChange={(value) => setFormState({ ...formState, subjective: value })}
      />
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
      <Button
        type="submit"
        disabled={disabled || !formState.started_at || !formState.reason.trim()}
      >
        <Save className="h-4 w-4" />
        {submitLabel}
      </Button>
    </form>
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
