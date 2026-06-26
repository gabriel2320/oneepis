"use client";

import Link from "next/link";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { ClinicalWorkspaceLayout } from "@/components/clinical/clinical-workspace";
import { ClinicalRiskPreview } from "@/components/clinical/clinical-risk-preview";
import { FullTimelinePreview } from "@/components/clinical/full-timeline-preview";
import { LabResultsPreview } from "@/components/clinical/lab-results-preview";
import { PatientAntecedentsPreview } from "@/components/clinical/patient-antecedents-preview";
import { PatientAiSuggestionsPanel } from "@/components/clinical/patient-ai-suggestions-panel";
import {
  AllergyList,
  ClinicalTimeline,
  CriticalAlerts,
  MedicationList,
  PatientLongitudinalSummary,
  QuickSoapEditor,
  VitalsStrip,
} from "@/components/clinical/patient-widgets";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  canManageClinicalEntries,
  canManageClinicalRisks,
  canManagePatient,
  canUseClinicalAi,
} from "@/lib/permissions";
import { careContextLabel } from "@/lib/patient-display";
import type { PatientRecordSnapshot } from "@/lib/types";

import { NoPermissionButton } from "./patient-page-shared";

export function PatientFichaWorkspace({
  patientId,
  record,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
}) {
  const { user } = useCurrentUser();
  const canWriteSoap = canManageClinicalEntries(user);
  const canUseAi = canUseClinicalAi(user);
  const canEditPatient = canManagePatient(user);
  const canWriteRisks = canManageClinicalRisks(user);

  return (
    <div className="space-y-4">
      <CriticalAlerts record={record} />
      <VitalsStrip vital={record.latest_vitals} />
      <FichaHeader patientId={patientId} canEditPatient={canEditPatient} />
      <PatientLongitudinalSummary record={record} />
      <PatientLongitudinalMap record={record} />
      <ClinicalWorkspaceLayout
        aside={
          <FichaContextRail
            patientId={patientId}
            record={record}
            canUseAi={canUseAi}
            canWriteRisks={canWriteRisks}
          />
        }
      >
        <ClinicalSectionCard
          title="Linea clinica longitudinal"
          description="Evoluciones recientes como cuerpo principal de la ficha."
          action={
            canWriteSoap ? (
              <QuickSoapEditor href={`/pacientes/${patientId}/evoluciones/nueva`} />
            ) : (
              <NoPermissionButton label="SOAP no permitido" />
            )
          }
        >
          <ClinicalTimeline entries={record.recent_entries} />
        </ClinicalSectionCard>
        <PatientAntecedentsPreview patientId={patientId} record={record} />
        <FullTimelinePreview patientId={patientId} />
      </ClinicalWorkspaceLayout>
    </div>
  );
}

function PatientLongitudinalMap({ record }: { record: PatientRecordSnapshot }) {
  const linkedEntries = record.recent_entries.filter((entry) => entry.encounter_id).length;
  const unlinkedEntries = record.recent_entries.length - linkedEntries;
  const longitudinalItems =
    record.active_problems.length +
    record.active_allergies.length +
    record.active_medications.length;

  return (
    <ClinicalSectionCard
      title="Mapa longitudinal del paciente"
      description="El paciente es unico; los episodios separan el contexto y la ficha reconcilia antecedentes."
    >
      <div className="grid gap-3 md:grid-cols-3">
        <LongitudinalMapItem
          label="Contexto operativo"
          value={careContextLabel(record.patient.current_care_context)}
          detail="Orienta el lugar de trabajo sin duplicar ficha."
        />
        <LongitudinalMapItem
          label="Actos con episodio"
          value={`${linkedEntries}`}
          detail={
            unlinkedEntries > 0
              ? `${unlinkedEntries} acto longitudinal sin episodio.`
              : "Evoluciones recientes vinculadas a contexto clinico."
          }
        />
        <LongitudinalMapItem
          label="Datos longitudinales"
          value={`${longitudinalItems}`}
          detail="Problemas, alergias y medicacion activa como contexto comun."
        />
      </div>
    </ClinicalSectionCard>
  );
}

function LongitudinalMapItem({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase text-muted-foreground">{label}</p>
        <Badge variant="outline">{value}</Badge>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}

function FichaHeader({
  patientId,
  canEditPatient,
}: {
  patientId: string;
  canEditPatient: boolean;
}) {
  return (
    <div className="flex flex-col gap-3 border-b pb-4 md:flex-row md:items-start md:justify-between">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold">Hoja clinica viva</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Lectura longitudinal del paciente: datos criticos arriba, evolucion clinica al centro
          y apoyo IA como riel contextual.
        </p>
      </div>
      <div className="flex flex-wrap gap-2" data-print-hidden="true">
        {canEditPatient ? (
          <Button asChild variant="outline" size="sm">
            <Link href={`/pacientes/${patientId}/estado`}>Editar estado</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Estado bloqueado" />
        )}
        <Button asChild variant="outline" size="sm">
          <Link href={`/print/pacientes/${patientId}/ficha`}>Ver papel</Link>
        </Button>
      </div>
    </div>
  );
}

function FichaContextRail({
  patientId,
  record,
  canUseAi,
  canWriteRisks,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  canUseAi: boolean;
  canWriteRisks: boolean;
}) {
  return (
    <>
      <ClinicalSectionCard title="Alergias">
        <AllergyList allergies={record.active_allergies} />
      </ClinicalSectionCard>
      <ClinicalSectionCard title="Medicacion activa">
        <MedicationList medications={record.active_medications} />
      </ClinicalSectionCard>
      <ClinicalRiskPreview patientId={patientId} canWrite={canWriteRisks} />
      <LabResultsPreview patientId={patientId} />
      <PatientAiSuggestionsPanel patientId={patientId} canUseAi={canUseAi} />
    </>
  );
}
