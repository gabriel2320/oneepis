"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { ErrorState, LoadingRows } from "@/components/clinical/states";
import { createHospitalDailySheet, updateHospitalDailySheet } from "@/lib/api/hospitalization";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageHospitalDailySheets } from "@/lib/permissions";
import type {
  HospitalDailySheet,
  HospitalDailySheetCreate,
  HospitalDailySheetUpdate,
} from "@/lib/types";

import {
  DailySheetForm,
  DailySheetList,
  emptyDailySheetForm,
  toDailySheetForm,
  toDailySheetPayload,
  type DailySheetFormState,
} from "./hospital-daily-sheet-widgets";
import { useHospitalDailySheets } from "./hospitalization-data";
import {
  BackLink,
  PageTitle,
  PatientLoadError,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function DailySheetPage() {
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
        <BackLink href="/hospitalizacion/camas" label="Camas hospitalarias" />
        <PageTitle
          title="Hoja diaria hospitalizada"
          description="Registro diario minimo, auditado y preparado para papel."
        />
        <DailySheetWorkspace patientId={patientId} />
      </div>
    </PatientClinicalShell>
  );
}

export function EditHospitalDailySheetPage() {
  const params = useParams<{ patientId: string; sheetId: string }>();
  const patientId = params.patientId;
  const sheetId = params.sheetId;
  const { record, recordQuery } = usePatientRecordQuery(patientId);
  const dailySheets = useHospitalDailySheets(patientId);
  const sheet = dailySheets.items.find((item) => item.id === sheetId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageHospitalDailySheets(user);

  if ((recordQuery.isLoading || dailySheets.isLoading) && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (!record) {
    return <PatientLoadError />;
  }

  return (
    <PatientClinicalShell record={record} activeSection="ficha">
      <div className="max-w-3xl space-y-5">
        <BackLink
          href={`/hospitalizacion/pacientes/${patientId}/hoja-diaria`}
          label="Hoja diaria"
        />
        <PageTitle
          title="Editar hoja diaria"
          description="Correccion manual auditada de un registro hospitalizado."
        />
        {!sheet ? <ErrorState description="No se encontro la hoja diaria solicitada." /> : null}
        {DEMO_MODE ? <ErrorState description="El modo demo no permite editar hojas reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite editar hoja diaria hospitalizada." />
        ) : null}
        {sheet?.status === "closed" ? (
          <ErrorState description="Esta hoja diaria esta cerrada. Puede revisarse e imprimirse, pero no editarse." />
        ) : null}
        {sheet ? (
          <EditDailySheetForm patientId={patientId} sheet={sheet} canWrite={canWrite} />
        ) : null}
      </div>
    </PatientClinicalShell>
  );
}

function EditDailySheetForm({
  patientId,
  sheet,
  canWrite,
}: {
  patientId: string;
  sheet: HospitalDailySheet;
  canWrite: boolean;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<DailySheetFormState>(() => toDailySheetForm(sheet));
  const isClosed = sheet.status === "closed";
  const mutation = useMutation({
    mutationFn: (payload: HospitalDailySheetUpdate) =>
      updateHospitalDailySheet(patientId, sheet.id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital-daily-sheets", patientId] });
      router.push(`/hospitalizacion/pacientes/${patientId}/hoja-diaria`);
    },
  });

  return (
    <ClinicalSectionCard title={`Hoja diaria ${sheet.sheet_date}`}>
      <DailySheetForm
        formState={formState}
        setFormState={setFormState}
        submitLabel={mutation.isPending ? "Guardando..." : "Guardar cambios"}
        disabled={mutation.isPending || DEMO_MODE || !canWrite || isClosed}
        onSubmit={() => mutation.mutate(toDailySheetPayload(formState))}
      />
      {mutation.isError ? (
        <p className="mt-3 text-sm text-destructive">No se pudo actualizar la hoja diaria.</p>
      ) : null}
    </ClinicalSectionCard>
  );
}

function DailySheetWorkspace({ patientId }: { patientId: string }) {
  const queryClient = useQueryClient();
  const dailySheets = useHospitalDailySheets(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageHospitalDailySheets(user);
  const [formState, setFormState] = useState<DailySheetFormState>(emptyDailySheetForm);
  const mutation = useMutation({
    mutationFn: (payload: HospitalDailySheetCreate) => createHospitalDailySheet(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital-daily-sheets", patientId] });
      setFormState(emptyDailySheetForm());
    },
  });

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
      <ClinicalSectionCard title="Hojas registradas">
        {dailySheets.isLoading ? <LoadingRows rows={3} /> : null}
        {dailySheets.isError ? (
          <ErrorState
            description="No se pudo cargar la hoja diaria hospitalizada."
            onRetry={dailySheets.refetch}
          />
        ) : null}
        {!dailySheets.isLoading && !dailySheets.isError ? (
          <DailySheetList sheets={dailySheets.items} patientId={patientId} />
        ) : null}
      </ClinicalSectionCard>
      <ClinicalSectionCard title="Nueva hoja diaria">
        {DEMO_MODE ? <ErrorState description="El modo demo no permite guardar hojas reales." /> : null}
        {!DEMO_MODE && !userLoading && !canWrite ? (
          <ErrorState description="Tu rol actual no permite crear hoja diaria hospitalizada." />
        ) : null}
        <DailySheetForm
          formState={formState}
          setFormState={setFormState}
          submitLabel={mutation.isPending ? "Guardando..." : "Guardar hoja diaria"}
          disabled={mutation.isPending || DEMO_MODE || !canWrite}
          onSubmit={() => mutation.mutate(toDailySheetPayload(formState))}
        />
        {mutation.isError ? (
          <p className="mt-3 text-sm text-destructive">
            No se pudo guardar. Verifica que exista un ingreso hospitalario activo.
          </p>
        ) : null}
      </ClinicalSectionCard>
    </div>
  );
}
