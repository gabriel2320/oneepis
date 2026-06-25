"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState, LoadingRows } from "@/components/clinical/states";
import {
  createHospitalIndication,
  updateHospitalIndication,
} from "@/lib/api/hospitalization";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageHospitalIndications } from "@/lib/permissions";
import type { HospitalIndication, HospitalIndicationCreate } from "@/lib/types";

import {
  HospitalIndicationForm,
  HospitalIndicationList,
  emptyHospitalIndicationForm,
  toHospitalIndicationPayload,
  type HospitalIndicationFormState,
} from "./hospital-indication-widgets";
import { useHospitalIndications } from "./hospitalization-data";
import {
  BackLink,
  PageTitle,
  PatientLoadError,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function HospitalIndicationsPage() {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="ficha">
      <div className="space-y-5">
        <BackLink href="/hospitalizacion/rondas" label="Rondas" />
        <PageTitle
          title="Indicaciones hospitalarias"
          description="Borradores auditados; no equivalen a orden firmada ni receta."
        />
        <HospitalIndicationWorkspace patientId={patientId} />
      </div>
    </PatientClinicalShell>
  );
}

function HospitalIndicationWorkspace({ patientId }: { patientId: string }) {
  const queryClient = useQueryClient();
  const indications = useHospitalIndications(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageHospitalIndications(user);
  const [formState, setFormState] =
    useState<HospitalIndicationFormState>(emptyHospitalIndicationForm);
  const [closingId, setClosingId] = useState<string | null>(null);
  const createMutation = useMutation({
    mutationFn: (payload: HospitalIndicationCreate) =>
      createHospitalIndication(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital-indications", patientId] });
      setFormState(emptyHospitalIndicationForm());
    },
  });
  const closeMutation = useMutation({
    mutationFn: (indication: HospitalIndication) =>
      updateHospitalIndication(patientId, indication.id, { status: "closed" }),
    onMutate: (indication) => setClosingId(indication.id),
    onSettled: async () => {
      setClosingId(null);
      await queryClient.invalidateQueries({ queryKey: ["hospital-indications", patientId] });
    },
  });

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
      <ClinicalSectionCard
        title="Borradores registrados"
        description="Lectura hospitalaria; cerrar bloquea edicion posterior."
      >
        {indications.isLoading ? <LoadingRows rows={3} /> : null}
        {indications.isError ? (
          <ErrorState
            description="No se pudieron cargar las indicaciones hospitalarias."
            onRetry={indications.refetch}
          />
        ) : null}
        {!indications.isLoading && !indications.isError ? (
          <HospitalIndicationList
            indications={indications.items}
            patientId={patientId}
            canWrite={!DEMO_MODE && canWrite}
            closingId={closingId}
            onClose={(indication) => closeMutation.mutate(indication)}
          />
        ) : null}
        {closeMutation.isError ? (
          <p className="mt-3 text-sm text-destructive">No se pudo cerrar el borrador.</p>
        ) : null}
        <div className="mt-4 rounded-md border border-dashed p-3">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold">Ejecucion bloqueada</p>
            <span className="rounded-md bg-warning/15 px-2 py-1 text-xs font-medium text-warning-foreground">
              No ejecutable
            </span>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            Requiere orden firmada, doble chequeo, MAR activo, registro de administracion y auditoria de ejecucion.
          </p>
        </div>
      </ClinicalSectionCard>
      <ClinicalSectionCard title="Nueva indicacion">
        {DEMO_MODE ? (
          <ErrorState description="El modo demo no permite guardar indicaciones reales." />
        ) : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite crear indicaciones hospitalarias." />
        ) : null}
        <HospitalIndicationForm
          formState={formState}
          setFormState={setFormState}
          submitLabel={createMutation.isPending ? "Guardando..." : "Guardar borrador"}
          disabled={createMutation.isPending || DEMO_MODE || !canWrite}
          onSubmit={() => createMutation.mutate(toHospitalIndicationPayload(formState))}
        />
        {createMutation.isError ? (
          <p className="mt-3 text-sm text-destructive">
            No se pudo guardar. Verifica que exista un ingreso hospitalario activo.
          </p>
        ) : null}
      </ClinicalSectionCard>
    </div>
  );
}
