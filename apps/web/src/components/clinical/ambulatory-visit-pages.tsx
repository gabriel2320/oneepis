"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ClinicalTimeline, EncounterList, PatientLongitudinalSummary } from "@/components/clinical/patient-widgets";
import { ErrorState, LoadingRows } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createClinicalEncounter,
  createClinicalEntry,
  listClinicalEncounters,
} from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { demoEncounters } from "@/lib/demo-record";
import { canManageClinicalEntries, canManageEncounters } from "@/lib/permissions";
import type { ClinicalEntry, PatientRecordSnapshot } from "@/lib/types";

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

type AmbulatoryVisitFormState = {
  started_at: string;
  reason: string;
  location_label: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

const emptyAmbulatoryVisitForm = (): AmbulatoryVisitFormState => ({
  started_at: toDatetimeLocal(new Date()),
  reason: "Atencion ambulatoria",
  location_label: "Consulta ambulatoria",
  subjective: "",
  objective: "",
  assessment: "",
  plan: "",
});

export function AmbulatoryVisitPage() {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="encuentros">
      <div className="space-y-5">
        <BackLink href="/consulta" label="Consulta" />
        <PageTitle
          title="Atencion ambulatoria"
          description="Encuentro ambulatorio y evolucion SOAP vinculada."
        />
        <AmbulatoryVisitWorkspace patientId={patientId} record={record} />
      </div>
    </PatientClinicalShell>
  );
}

function AmbulatoryVisitWorkspace({
  patientId,
  record,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
}) {
  const queryClient = useQueryClient();
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageEncounters(user) && canManageClinicalEntries(user);
  const [formState, setFormState] = useState<AmbulatoryVisitFormState>(
    emptyAmbulatoryVisitForm,
  );
  const [savedEntry, setSavedEntry] = useState<ClinicalEntry | null>(null);
  const encountersQuery = useQuery({
    queryKey: ["clinical-encounters", patientId],
    queryFn: () => listClinicalEncounters(patientId),
    enabled: !DEMO_MODE,
  });
  const encounters = DEMO_MODE
    ? demoEncounters.filter((encounter) => encounter.patient_id === patientId)
    : (encountersQuery.data ?? []);
  const ambulatoryEncounters = encounters.filter((encounter) => encounter.type === "ambulatory");
  const mutation = useMutation({
    mutationFn: async (payload: AmbulatoryVisitFormState) => {
      const startedAt = new Date(payload.started_at).toISOString();
      const encounter = await createClinicalEncounter(patientId, {
        type: "ambulatory",
        status: "in_progress",
        reason: payload.reason,
        started_at: startedAt,
        location_label: emptyToNull(payload.location_label),
        notes: "Creado desde atencion ambulatoria.",
      });
      return createClinicalEntry(patientId, {
        encounter_id: encounter.id,
        kind: "progress",
        status: "draft",
        occurred_at: startedAt,
        title: payload.reason,
        subjective: emptyToNull(payload.subjective),
        objective: emptyToNull(payload.objective),
        assessment: emptyToNull(payload.assessment),
        plan: emptyToNull(payload.plan),
        tags: ["ambulatory", "soap"],
      });
    },
    onSuccess: async (entry) => {
      setSavedEntry(entry);
      setFormState(emptyAmbulatoryVisitForm());
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["patient-record", patientId] }),
        queryClient.invalidateQueries({ queryKey: ["clinical-encounters", patientId] }),
      ]);
    },
  });

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
      <div className="space-y-5">
        <ClinicalSectionCard title="Resumen longitudinal">
          <PatientLongitudinalSummary record={record} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Encuentros ambulatorios">
          {encountersQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
          {encountersQuery.isError && !DEMO_MODE ? (
            <ErrorState
              description="No se pudieron cargar los encuentros ambulatorios."
              onRetry={() => encountersQuery.refetch()}
            />
          ) : null}
          {!encountersQuery.isLoading || DEMO_MODE ? (
            <EncounterList encounters={ambulatoryEncounters} />
          ) : null}
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Evoluciones recientes">
          <ClinicalTimeline entries={record.recent_entries} />
        </ClinicalSectionCard>
      </div>
      <ClinicalSectionCard
        title="Nueva atencion"
        description="Guarda encuentro ambulatorio y SOAP como borrador auditable."
      >
        {DEMO_MODE ? (
          <ErrorState description="El modo demo no permite guardar atenciones reales." />
        ) : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite crear atencion ambulatoria." />
        ) : null}
        <AmbulatoryVisitForm
          formState={formState}
          setFormState={setFormState}
          disabled={mutation.isPending || DEMO_MODE || !canWrite}
          submitLabel={mutation.isPending ? "Guardando..." : "Guardar atencion"}
          onSubmit={() => mutation.mutate(formState)}
        />
        {mutation.isError ? (
          <p className="mt-3 text-sm text-destructive">
            No se pudo guardar la atencion. Revisa API y permisos.
          </p>
        ) : null}
        {savedEntry ? (
          <p className="mt-3 text-sm text-muted-foreground">
            Borrador SOAP vinculado: {savedEntry.title}
          </p>
        ) : null}
      </ClinicalSectionCard>
    </div>
  );
}

function AmbulatoryVisitForm({
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
