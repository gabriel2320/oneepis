"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Printer, Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { HospitalClinicalShell } from "@/components/clinical/clinical-domain-shell";
import { formatDateTime } from "@/components/clinical/date-format";
import { HistoricalDiagnosisContextCard } from "@/components/clinical/historical-diagnosis-context";
import { PatientClinicalLoading } from "@/components/clinical/patient-clinical-shell";
import { EmptyState, ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createClinicalEntry, listClinicalEncounters } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { demoEncounters } from "@/lib/demo-record";
import { activeHospitalizationEncounters } from "@/lib/hospitalization-workflows";
import { canManageClinicalEntries } from "@/lib/permissions";
import type { ClinicalEncounter, ClinicalEntry, PatientRecordSnapshot } from "@/lib/types";

import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  toDatetimeLocal,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

type DischargeFormState = {
  encounter_id: string;
  occurred_at: string;
  title: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

const emptyDischargeForm = (): DischargeFormState => ({
  encounter_id: "",
  occurred_at: toDatetimeLocal(new Date()),
  title: "Epicrisis preliminar",
  subjective: "",
  objective: "",
  assessment: "",
  plan: "",
});

export function HospitalDischargeSummaryPage() {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <HospitalClinicalShell record={record} activeSection="epicrisis">
      <div className="space-y-5">
        <BackLink href="/hospitalizacion/rondas" label="Evolucion diaria" />
        <PageTitle
          title="Alta y epicrisis"
          description="Borrador de egreso hospitalario vinculado a una hospitalizacion activa."
        />
        <DischargeSummaryWorkspace patientId={patientId} record={record} />
      </div>
    </HospitalClinicalShell>
  );
}

function DischargeSummaryWorkspace({
  patientId,
  record,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
}) {
  const queryClient = useQueryClient();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageClinicalEntries(user);
  const [formState, setFormState] = useState<DischargeFormState>(emptyDischargeForm);
  const encountersQuery = useQuery({
    queryKey: ["clinical-encounters", patientId],
    queryFn: () => listClinicalEncounters(patientId),
    enabled: !DEMO_MODE,
  });
  const encounters = DEMO_MODE
    ? demoEncounters.filter((encounter) => encounter.patient_id === patientId)
    : (encountersQuery.data ?? []);
  const hospitalEncounters = activeHospitalizationEncounters(encounters);
  const selectedEncounterId = formState.encounter_id || hospitalEncounters[0]?.id || "";
  const dischargeEntries = record.recent_entries.filter((entry) => entry.kind === "discharge_summary");
  const mutation = useMutation({
    mutationFn: (payload: DischargeFormState) =>
      createClinicalEntry(patientId, {
        encounter_id: payload.encounter_id,
        kind: "discharge_summary",
        status: "draft",
        occurred_at: new Date(payload.occurred_at).toISOString(),
        title: payload.title,
        subjective: emptyToNull(payload.subjective),
        objective: emptyToNull(payload.objective),
        assessment: emptyToNull(payload.assessment),
        plan: emptyToNull(payload.plan),
        tags: ["hospitalization", "discharge_summary"],
      }),
    onSuccess: async () => {
      setFormState(emptyDischargeForm());
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
    },
  });

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
      <div className="space-y-5">
        <HistoricalDiagnosisContextCard
          diagnoses={record.historical_diagnoses}
          title="Contexto historico para epicrisis"
          description="Antecedentes historicos disponibles para revisar antes de redactar; no completan diagnosticos de egreso."
        />
        <ClinicalSectionCard title="Epicrisis registradas">
          <DischargeSummaryList patientId={patientId} entries={dischargeEntries} />
        </ClinicalSectionCard>
      </div>
      <ClinicalSectionCard
        title="Borrador de epicrisis"
        description="No equivale a firma de alta ni documento legal; se imprime como desarrollo."
      >
        {DEMO_MODE ? <ErrorState description="El modo demo no permite guardar epicrisis reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu perfil no tiene permiso para crear epicrisis hospitalaria." />
        ) : null}
        {encountersQuery.isError && !DEMO_MODE ? (
          <ErrorState
            description="No se pudieron cargar ingresos hospitalarios."
            onRetry={() => encountersQuery.refetch()}
          />
        ) : null}
        {hospitalEncounters.length === 0 ? (
          <EmptyState
            title="Sin hospitalizacion activa"
            description="La epicrisis debe vincularse a un encuentro hospitalario antes de redactarse."
          />
        ) : null}
        <DischargeSummaryForm
          formState={{ ...formState, encounter_id: selectedEncounterId }}
          setFormState={setFormState}
          encounters={hospitalEncounters}
          disabled={mutation.isPending || DEMO_MODE || !canWrite || hospitalEncounters.length === 0}
          submitLabel={mutation.isPending ? "Guardando..." : "Guardar epicrisis"}
          onSubmit={() => mutation.mutate({ ...formState, encounter_id: selectedEncounterId })}
        />
        {mutation.isError ? (
          <p className="mt-3 text-sm text-destructive">
            No se pudo guardar. Verifica que el encuentro pertenezca al paciente.
          </p>
        ) : null}
      </ClinicalSectionCard>
    </div>
  );
}

function DischargeSummaryList({ patientId, entries }: { patientId: string; entries: ClinicalEntry[] }) {
  if (entries.length === 0) {
    return (
      <EmptyState
        title="Sin epicrisis registrada"
        description="El primer borrador aparecera aqui y tendra papel carta propio."
      />
    );
  }

  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <article key={entry.id} className="rounded-md border p-3">
          <p className="text-sm font-semibold">{entry.title}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {formatDateTime(entry.occurred_at)} - Estado:{" "}
            {entry.status === "draft" ? "Borrador" : entry.status}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            {entry.assessment || entry.plan || "Epicrisis sin diagnostico de egreso."}
          </p>
          <Button asChild className="mt-3" variant="outline" size="sm">
            <Link href={`/print/hospitalizacion/pacientes/${patientId}/epicrisis/${entry.id}`}>
              <Printer className="h-4 w-4" />
              Ver papel
            </Link>
          </Button>
        </article>
      ))}
    </div>
  );
}

function DischargeSummaryForm({
  formState,
  setFormState,
  encounters,
  disabled,
  submitLabel,
  onSubmit,
}: {
  formState: DischargeFormState;
  setFormState: (value: DischargeFormState) => void;
  encounters: ClinicalEncounter[];
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
      <Field label="Hospitalizacion">
        <select
          aria-label="Hospitalizacion para epicrisis"
          className="h-9 w-full rounded-md border bg-background px-3 text-sm"
          disabled={disabled}
          value={formState.encounter_id}
          onChange={(event) => setFormState({ ...formState, encounter_id: event.target.value })}
        >
          {encounters.map((encounter) => (
            <option key={encounter.id} value={encounter.id}>
              {encounter.reason} - {formatDateTime(encounter.started_at)}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Fecha de egreso">
        <Input
          type="datetime-local"
          disabled={disabled}
          value={formState.occurred_at}
          onChange={(event) => setFormState({ ...formState, occurred_at: event.target.value })}
        />
      </Field>
      <Field label="Titulo">
        <Input
          disabled={disabled}
          value={formState.title}
          onChange={(event) => setFormState({ ...formState, title: event.target.value })}
        />
      </Field>
      <DischargeTextArea label="Motivo de ingreso y antecedentes" value={formState.subjective} disabled={disabled} onChange={(value) => setFormState({ ...formState, subjective: value })} />
      <DischargeTextArea label="Evolucion intrahospitalaria" value={formState.objective} disabled={disabled} onChange={(value) => setFormState({ ...formState, objective: value })} />
      <DischargeTextArea label="Diagnosticos de egreso" value={formState.assessment} disabled={disabled} onChange={(value) => setFormState({ ...formState, assessment: value })} />
      <DischargeTextArea label="Plan de alta y seguimiento" value={formState.plan} disabled={disabled} onChange={(value) => setFormState({ ...formState, plan: value })} />
      <Button type="submit" disabled={disabled || !formState.encounter_id || !formState.title.trim()}>
        <Save className="h-4 w-4" />
        {submitLabel}
      </Button>
    </form>
  );
}

function DischargeTextArea({
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
      <Textarea disabled={disabled} value={value} onChange={(event) => onChange(event.target.value)} />
    </Field>
  );
}
