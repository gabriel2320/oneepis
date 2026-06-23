"use client";

import Link from "next/link";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AiInsightPanel } from "@/components/clinical/ai-insight-panel";
import { AiSafetyPanel } from "@/components/clinical/ai-safety-panel";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { FullTimelinePreview } from "@/components/clinical/full-timeline-preview";
import { LabResultsPreview } from "@/components/clinical/lab-results-preview";
import { PatientAntecedentsPreview } from "@/components/clinical/patient-antecedents-preview";
import { PatientClinicalLoading, PatientClinicalShell } from "@/components/clinical/patient-clinical-shell";
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
  MedicationList,
  PatientLongitudinalSummary,
  QuickSoapEditor,
  VitalsStrip,
} from "@/components/clinical/patient-widgets";
import { EmptyState, ErrorState } from "@/components/clinical/states";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
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
        <CriticalAlerts record={record} />
        <VitalsStrip vital={record.latest_vitals} />
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
        <PatientLongitudinalSummary record={record} />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="space-y-4">
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
          </div>
          <aside className="space-y-4">
            <ClinicalSectionCard title="Alergias">
              <AllergyList allergies={record.active_allergies} />
            </ClinicalSectionCard>
            <ClinicalSectionCard title="Medicacion activa">
              <MedicationList medications={record.active_medications} />
            </ClinicalSectionCard>
            <LabResultsPreview patientId={patientId} />
            <PatientAiSuggestionsPanel patientId={patientId} canUseAi={canUseAi} />
          </aside>
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
        title="Pantalla preparada: documentos sin uploads reales"
        description="Se habilitara cuando existan autenticacion, permisos y politica PHI; no simula flujo productivo."
      />
    </ClinicalSectionCard>
  );
}
