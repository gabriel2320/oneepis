"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AmbulatoryClosePanel } from "@/components/clinical/ambulatory-close-panel";
import { AmbulatoryPreconsultPanel } from "@/components/clinical/ambulatory-preconsult-panel";
import {
  AmbulatoryVisitForm,
  type AmbulatoryVisitFormState,
} from "@/components/clinical/ambulatory-visit-form";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { AmbulatoryClinicalShell } from "@/components/clinical/clinical-domain-shell";
import { PatientClinicalLoading } from "@/components/clinical/patient-clinical-shell";
import { ClinicalTimeline, EncounterList, PatientLongitudinalSummary } from "@/components/clinical/patient-widgets";
import { ErrorState, LoadingRows } from "@/components/clinical/states";
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
  PageTitle,
  PatientLoadError,
  emptyToNull,
  toDatetimeLocal,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

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
    <AmbulatoryClinicalShell record={record} activeSection="atencion-ambulatoria">
      <div className="space-y-5">
        <BackLink href="/consulta" label="Consulta" />
        <PageTitle
          title="Atencion ambulatoria"
          description="Atencion clinica ambulatoria con evolucion vinculada."
        />
        <AmbulatoryVisitWorkspace patientId={patientId} record={record} />
      </div>
    </AmbulatoryClinicalShell>
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
        <ClinicalSectionCard
          title="Atencion clinica"
          description="Registro principal ambulatorio: motivo, evaluacion y plan en una atencion auditable."
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
        <AmbulatoryClosePanel
          patientId={patientId}
          encounters={ambulatoryEncounters}
          disabled={DEMO_MODE || !canWrite}
        />
      </div>
      <div className="space-y-5">
        <AmbulatoryPreconsultPanel patientId={patientId} />
        <ClinicalSectionCard title="Contexto longitudinal">
          <PatientLongitudinalSummary record={record} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Atenciones previas">
          {encountersQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
          {encountersQuery.isError && !DEMO_MODE ? (
            <ErrorState
              description="No se pudieron cargar las atenciones ambulatorias."
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
    </div>
  );
}
