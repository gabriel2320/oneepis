"use client";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AiInsightPanel } from "@/components/clinical/ai-insight-panel";
import { AiSafetyPanel } from "@/components/clinical/ai-safety-panel";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { StructuredAntecedentsReadModel } from "@/components/clinical/patient-antecedents-read-model";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
import { PatientFormalCover } from "@/components/clinical/patient-formal-cover";
import {
  AllergyWorkspace,
  AuditWorkspace,
  EncounterWorkspace,
  MedicationWorkspace,
  PatientAiSuggestionsPanel,
  ProblemWorkspace,
  VitalsWorkspace,
} from "@/components/clinical/patient-record-workspaces";
import {
  AllergyList,
  ClinicalTimeline,
  CriticalAlerts,
  EncounterTraceSummary,
  MedicationList,
  PatientLongitudinalSummary,
  QuickSoapEditor,
  VitalsStrip,
} from "@/components/clinical/patient-widgets";
import { EmptyState, ErrorState } from "@/components/clinical/states";
import { AppShell } from "@/components/layout/app-shell";
import { DEMO_MODE } from "@/lib/api/client";
import { canManageClinicalEntries, canManagePatient, canUseClinicalAi } from "@/lib/permissions";
import type { PatientRecordSnapshot } from "@/lib/types";

import {
  NoPermissionButton,
  type PatientSection,
  usePatientId,
  usePatientRecordQuery,
} from "./patient-page-shared";

export function PatientRecordScreen({ section = "ficha" }: { section?: PatientSection }) {
  const patientId = usePatientId();
  const { record, recordQuery } = usePatientRecordQuery(patientId);

  if (recordQuery.isLoading && !DEMO_MODE) {
    return <PatientClinicalLoading />;
  }

  if (recordQuery.isError && !DEMO_MODE) {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl p-4 md:p-6">
          <ErrorState
            description="No se pudo cargar la ficha del paciente."
            onRetry={() => recordQuery.refetch()}
          />
        </div>
      </AppShell>
    );
  }

  if (!record) {
    return <PatientClinicalLoading />;
  }

  return (
    <PatientClinicalShell record={record} activeSection={section}>
      <PatientSectionContent record={record} section={section} patientId={patientId} />
    </PatientClinicalShell>
  );
}

function PatientSectionContent({
  record,
  section,
  patientId,
}: {
  record: PatientRecordSnapshot;
  section: PatientSection;
  patientId: string;
}) {
  const { user } = useCurrentUser();
  const canWriteSoap = canManageClinicalEntries(user);
  const canUseAi = canUseClinicalAi(user);
  const canEditPatient = canManagePatient(user);

  if (section === "ficha") {
    return (
      <div className="space-y-4">
        <PatientFormalCover record={record} patientId={patientId} canEditPatient={canEditPatient} />
        <CriticalAlerts record={record} />
        <VitalsStrip vital={record.latest_vitals} />
        <EncounterTraceSummary record={record} patientId={patientId} />
        <PatientLongitudinalSummary record={record} />
        <ClinicalSectionCard
          title="Antecedentes estructurados"
          description="Read-model de problemas, alergias y medicacion activa desde sus fuentes."
        >
          <StructuredAntecedentsReadModel record={record} patientId={patientId} />
        </ClinicalSectionCard>
        <div className="grid gap-4 xl:grid-cols-[1fr_380px]">
          <ClinicalSectionCard
            title="Linea clinica"
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
          <div className="space-y-4">
            <ClinicalSectionCard title="Alergias">
              <AllergyList allergies={record.active_allergies} />
            </ClinicalSectionCard>
            <ClinicalSectionCard title="Medicacion activa">
              <MedicationList medications={record.active_medications} />
            </ClinicalSectionCard>
            <PatientAiSuggestionsPanel patientId={patientId} canUseAi={canUseAi} />
          </div>
        </div>
      </div>
    );
  }

  if (section === "evoluciones") {
    return (
      <ClinicalSectionCard
        title="Evoluciones"
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
    );
  }

  if (section === "encuentros") {
    return <EncounterWorkspace patientId={patientId} user={user} />;
  }

  if (section === "alergias") {
    return <AllergyWorkspace patientId={patientId} record={record} user={user} />;
  }

  if (section === "medicacion") {
    return <MedicationWorkspace patientId={patientId} record={record} user={user} />;
  }

  if (section === "signos-vitales") {
    return <VitalsWorkspace patientId={patientId} record={record} user={user} />;
  }

  if (section === "ia") {
    if (!canUseAi) {
      return (
        <ClinicalSectionCard title="IA clinica">
          <EmptyState
            title="IA no permitida para este rol"
            description="Las sugerencias clinicas quedan disponibles para medico, admin o dev."
          />
        </ClinicalSectionCard>
      );
    }
    return (
      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <AiInsightPanel />
        <AiSafetyPanel />
      </div>
    );
  }

  if (section === "auditoria") {
    return <AuditWorkspace patientId={patientId} />;
  }

  if (section === "problemas") {
    return <ProblemWorkspace patientId={patientId} record={record} user={user} />;
  }

  return (
    <ClinicalSectionCard title="Documentos">
      <EmptyState
        title="Documentos sin uploads reales"
        description="Se habilitara cuando existan autenticacion, permisos y politica PHI."
      />
    </ClinicalSectionCard>
  );
}
