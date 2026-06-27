"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Printer, Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { HospitalClinicalShell } from "@/components/clinical/clinical-domain-shell";
import { formatDateTime } from "@/components/clinical/date-format";
import { PatientClinicalLoading } from "@/components/clinical/patient-clinical-shell";
import { EmptyState, ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createClinicalEntry,
  listClinicalEncounters,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { demoEncounters } from "@/lib/demo-record";
import { activeHospitalizationEncounters } from "@/lib/hospitalization-workflows";
import { canManageClinicalEntries } from "@/lib/permissions";
import type { ClinicalEncounter, ClinicalEntry } from "@/lib/types";

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

type AdmissionFormState = {
  encounter_id: string;
  occurred_at: string;
  title: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

const emptyAdmissionForm = (): AdmissionFormState => ({
  encounter_id: "",
  occurred_at: toDatetimeLocal(new Date()),
  title: "Ingreso medico hospitalario",
  subjective: "",
  objective: "",
  assessment: "",
  plan: "",
});

export function HospitalAdmissionPage() {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <HospitalClinicalShell record={record} activeSection="ingreso-hospitalario">
      <div className="space-y-5">
        <BackLink href="/hospitalizacion/rondas" label="Evolucion diaria" />
        <PageTitle
          title="Ingreso medico hospitalario"
          description="Borrador clinico vinculado a un encuentro hospitalario activo."
        />
        <HospitalAdmissionWorkspace patientId={patientId} entries={record.recent_entries} />
      </div>
    </HospitalClinicalShell>
  );
}

function HospitalAdmissionWorkspace({
  patientId,
  entries,
}: {
  patientId: string;
  entries: ClinicalEntry[];
}) {
  const queryClient = useQueryClient();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageClinicalEntries(user);
  const [formState, setFormState] = useState<AdmissionFormState>(emptyAdmissionForm);
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
  const admissionEntries = entries.filter((entry) => entry.kind === "intake");
  const mutation = useMutation({
    mutationFn: (payload: AdmissionFormState) =>
      createClinicalEntry(patientId, {
        encounter_id: payload.encounter_id,
        kind: "intake",
        status: "draft",
        occurred_at: new Date(payload.occurred_at).toISOString(),
        title: payload.title,
        subjective: emptyToNull(payload.subjective),
        objective: emptyToNull(payload.objective),
        assessment: emptyToNull(payload.assessment),
        plan: emptyToNull(payload.plan),
        tags: ["hospitalization", "intake"],
      }),
    onSuccess: async () => {
      setFormState(emptyAdmissionForm());
      await queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] });
    },
  });

  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
        <ClinicalSectionCard title="Ingresos registrados">
          <AdmissionEntryList patientId={patientId} entries={admissionEntries} />
        </ClinicalSectionCard>
        <ClinicalSectionCard
          title="Borrador de ingreso"
          description="No equivale a firma ni documento legal; se imprime como desarrollo."
        >
          {DEMO_MODE ? <ErrorState description="El modo demo no permite guardar ingresos reales." /> : null}
          {!DEMO_MODE && !userLoading && !canWrite ? (
            <ErrorState description="Tu perfil no tiene permiso para crear ingreso medico hospitalario." />
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
              description="Crea o abre un encuentro hospitalario antes de registrar ingreso medico."
            />
          ) : null}
          <AdmissionForm
            formState={{ ...formState, encounter_id: selectedEncounterId }}
            setFormState={setFormState}
            encounters={hospitalEncounters}
            disabled={mutation.isPending || DEMO_MODE || !canWrite || hospitalEncounters.length === 0}
            submitLabel={mutation.isPending ? "Guardando..." : "Guardar ingreso"}
            onSubmit={() => mutation.mutate({ ...formState, encounter_id: selectedEncounterId })}
          />
          {mutation.isError ? (
            <p className="mt-3 text-sm text-destructive">
              No se pudo guardar. Verifica que el encuentro pertenezca al paciente.
            </p>
          ) : null}
        </ClinicalSectionCard>
      </div>
    </div>
  );
}

function AdmissionEntryList({
  patientId,
  entries,
}: {
  patientId: string;
  entries: ClinicalEntry[];
}) {
  if (entries.length === 0) {
    return (
      <EmptyState
        title="Sin ingreso medico registrado"
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
            {formatDateTime(entry.occurred_at)} - Estado: {entry.status}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            {entry.assessment || entry.subjective || "Ingreso sin resumen clinico."}
          </p>
          <Button asChild className="mt-3" variant="outline" size="sm">
            <Link href={`/print/hospitalizacion/pacientes/${patientId}/ingreso/${entry.id}`}>
              <Printer className="h-4 w-4" />
              Ver papel
            </Link>
          </Button>
        </article>
      ))}
    </div>
  );
}

function AdmissionForm({
  formState,
  setFormState,
  encounters,
  disabled,
  submitLabel,
  onSubmit,
}: {
  formState: AdmissionFormState;
  setFormState: (value: AdmissionFormState) => void;
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
          aria-label="Hospitalizacion activa"
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
      <Field label="Fecha y hora">
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
      <AdmissionTextArea label="Motivo y antecedentes" value={formState.subjective} disabled={disabled} onChange={(value) => setFormState({ ...formState, subjective: value })} />
      <AdmissionTextArea label="Examen fisico" value={formState.objective} disabled={disabled} onChange={(value) => setFormState({ ...formState, objective: value })} />
      <AdmissionTextArea label="Impresion diagnostica" value={formState.assessment} disabled={disabled} onChange={(value) => setFormState({ ...formState, assessment: value })} />
      <AdmissionTextArea label="Plan inicial" value={formState.plan} disabled={disabled} onChange={(value) => setFormState({ ...formState, plan: value })} />
      <Button type="submit" disabled={disabled || !formState.encounter_id || !formState.title.trim()}>
        <Save className="h-4 w-4" />
        {submitLabel}
      </Button>
    </form>
  );
}

function AdmissionTextArea({
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
