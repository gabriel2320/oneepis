"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Printer, Save } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { HospitalizationBoardContent } from "@/components/clinical/hospital-bed-pages";
import { RoundList } from "@/components/clinical/hospitalization-widgets";
import { useHospitalizationBoard } from "@/components/clinical/hospitalization-data";
import { ModulePage } from "@/components/clinical/module-pages";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createHospitalDailySheet } from "@/lib/api/hospitalization";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageHospitalDailySheets } from "@/lib/permissions";
import type { HospitalDailySheet, HospitalDailySheetCreate } from "@/lib/types";

import { formatDateTime } from "./date-format";
import { useHospitalDailySheets } from "./hospitalization-data";
import {
  BackLink,
  Field,
  PageTitle,
  PatientLoadError,
  emptyToNull,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function HospitalHomePage() {
  const board = useHospitalizationBoard();

  return (
    <ModulePage
      title="Hospitalizacion"
      description="Base para camas, rondas, hoja diaria e indicaciones."
      actions={[
        { href: "/hospitalizacion/camas", label: "Camas" },
        { href: "/hospitalizacion/rondas", label: "Rondas" },
      ]}
    >
      <div className="grid gap-4 xl:grid-cols-2">
        <ClinicalSectionCard title="Camas">
          <HospitalizationBoardContent board={board} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Rondas">
          <RoundList />
        </ClinicalSectionCard>
      </div>
    </ModulePage>
  );
}

export function HospitalRoundsPage() {
  return (
    <ModulePage title="Rondas" description="Lista de rondas para pacientes hospitalizados.">
      <ClinicalSectionCard title="RoundList">
        <RoundList />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

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

export function OrdersPage() {
  return (
    <ModulePage title="Indicaciones" description="Base para indicaciones hospitalarias auditadas.">
      <ClinicalSectionCard title="Indicaciones">
        <EmptyState title="Indicaciones pendientes" description="Requiere permisos y firma clinica." />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

function DailySheetWorkspace({ patientId }: { patientId: string }) {
  const queryClient = useQueryClient();
  const dailySheets = useHospitalDailySheets(patientId);
  const { user, isLoading: userLoading } = useCurrentUser();
  const canWrite = canManageHospitalDailySheets(user);
  const [formState, setFormState] = useState({
    sheet_date: new Date().toISOString().slice(0, 10),
    clinical_summary: "",
    overnight_events: "",
    active_plan: "",
    pending_tasks: "",
    safety_notes: "",
  });
  const mutation = useMutation({
    mutationFn: (payload: HospitalDailySheetCreate) => createHospitalDailySheet(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital-daily-sheets", patientId] });
      setFormState((current) => ({
        ...current,
        clinical_summary: "",
        overnight_events: "",
        active_plan: "",
        pending_tasks: "",
        safety_notes: "",
      }));
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
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate({
              sheet_date: formState.sheet_date,
              clinical_summary: formState.clinical_summary,
              overnight_events: emptyToNull(formState.overnight_events),
              active_plan: emptyToNull(formState.active_plan),
              pending_tasks: emptyToNull(formState.pending_tasks),
              safety_notes: emptyToNull(formState.safety_notes),
            });
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
              onChange={(event) =>
                setFormState({ ...formState, pending_tasks: event.target.value })
              }
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
            disabled={
              mutation.isPending ||
              DEMO_MODE ||
              !canWrite ||
              !formState.sheet_date ||
              !formState.clinical_summary.trim()
            }
          >
            <Save className="h-4 w-4" />
            {mutation.isPending ? "Guardando..." : "Guardar hoja diaria"}
          </Button>
          {mutation.isError ? (
            <p className="text-sm text-destructive">
              No se pudo guardar. Verifica que exista un ingreso hospitalario activo.
            </p>
          ) : null}
        </form>
      </ClinicalSectionCard>
    </div>
  );
}

function DailySheetList({
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
            <Button asChild variant="outline" size="sm">
              <Link
                href={`/print/hospitalizacion/pacientes/${patientId}/hoja-diaria/${sheet.id}`}
              >
                <Printer className="h-4 w-4" />
                Imprimir
              </Link>
            </Button>
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
