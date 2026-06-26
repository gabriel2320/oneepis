"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { AuditTimeline } from "@/components/clinical/audit-widgets";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { MedicationVademecumPanel } from "@/components/clinical/medication-vademecum-panel";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import {
  AllergyList,
  EncounterList,
  LatestVitalsTrend,
  MedicationList,
  ProblemList,
  VitalsStrip,
} from "@/components/clinical/patient-widgets";
import { Button } from "@/components/ui/button";
import { listAuditEvents, listClinicalEncounters, listVitalSigns } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import { demoEncounters } from "@/lib/demo-record";
import {
  canManageAllergies,
  canManageEncounters,
  canManageMedications,
  canManageProblems,
  canRecordVitals,
} from "@/lib/permissions";
import type { AuthUser, PatientRecordSnapshot } from "@/lib/types";

import { NoPermissionButton } from "./patient-page-shared";

export function EncounterWorkspace({ patientId, user }: { patientId: string; user: AuthUser | null }) {
  const canWrite = canManageEncounters(user);
  const encountersQuery = useQuery({
    queryKey: ["clinical-encounters", patientId],
    queryFn: () => listClinicalEncounters(patientId),
    enabled: !DEMO_MODE,
  });
  const encounters = DEMO_MODE
    ? demoEncounters.filter((encounter) => encounter.patient_id === patientId)
    : encountersQuery.data;

  return (
    <ClinicalSectionCard
      title="Atenciones e ingresos vinculados"
      description="Dato de soporte para otros flujos; la ficha principal se centra en evoluciones y documentos clinicos."
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/encuentros/nuevo`}>Registrar soporte</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      {encountersQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
      {encountersQuery.isError && !DEMO_MODE ? (
        <ErrorState description="No se pudieron cargar las atenciones e ingresos." onRetry={() => encountersQuery.refetch()} />
      ) : null}
      {encounters ? <EncounterList encounters={encounters} /> : null}
    </ClinicalSectionCard>
  );
}

export function AllergyWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canManageAllergies(user);
  return (
    <ClinicalSectionCard
      title="Alergias registradas"
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/alergias/nueva`}>Agregar</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      <AllergyList allergies={record.active_allergies} />
    </ClinicalSectionCard>
  );
}

export function MedicationWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canManageMedications(user);
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      <ClinicalSectionCard
        title="Medicacion"
        description="Lista activa; receta y orden ejecutable siguen bloqueadas."
        action={
          canWrite ? (
            <Button asChild size="sm">
              <Link href={`/pacientes/${patientId}/medicacion/nueva`}>Agregar</Link>
            </Button>
          ) : (
            <NoPermissionButton label="Sin permiso" />
          )
        }
      >
        <MedicationList medications={record.active_medications} />
      </ClinicalSectionCard>
      <MedicationVademecumPanel patientId={patientId} canWrite={canWrite} />
    </div>
  );
}

export function ProblemWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canManageProblems(user);
  return (
    <ClinicalSectionCard
      title="Antecedentes clinicos activos"
      description="Dato longitudinal usado como contexto en evolucion, indicaciones, receta bloqueada y resumen."
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/problemas/nuevo`}>Agregar</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      <ProblemList problems={record.active_problems} />
    </ClinicalSectionCard>
  );
}

export function VitalsWorkspace({
  patientId,
  record,
  user,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
  user: AuthUser | null;
}) {
  const canWrite = canRecordVitals(user);
  const vitalsQuery = useQuery({
    queryKey: ["vital-signs", patientId],
    queryFn: () => listVitalSigns(patientId),
    enabled: !DEMO_MODE,
  });
  const vitals = DEMO_MODE ? (record.latest_vitals ? [record.latest_vitals] : []) : (vitalsQuery.data ?? []);

  return (
    <div className="space-y-4">
      <VitalsStrip vital={record.latest_vitals} />
      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <ClinicalSectionCard title="Tendencia">
          <LatestVitalsTrend vitals={vitals} />
        </ClinicalSectionCard>
        <ClinicalSectionCard
          title="Nuevo control"
          description="Cada registro se captura en una pantalla dedicada."
          action={
            canWrite ? (
              <Button asChild size="sm">
                <Link href={`/pacientes/${patientId}/signos-vitales/nuevo`}>Registrar</Link>
              </Button>
            ) : (
              <NoPermissionButton label="Sin permiso" />
            )
          }
        >
          <EmptyState title="Accion separada" description="Usa registrar para abrir el formulario de signos." />
        </ClinicalSectionCard>
      </div>
    </div>
  );
}

export function AuditWorkspace({ patientId }: { patientId: string }) {
  const auditQuery = useQuery({
    queryKey: ["audit-events", patientId],
    queryFn: () => listAuditEvents(patientId),
    enabled: !DEMO_MODE,
  });

  return (
    <ClinicalSectionCard title="Auditoria">
      {DEMO_MODE ? (
        <EmptyState title="Auditoria no disponible en demo" description="Usa la API real para ver eventos." />
      ) : null}
      {auditQuery.isLoading ? <LoadingRows rows={4} /> : null}
      {auditQuery.isError ? (
        <ErrorState description="No se pudo cargar auditoria." onRetry={() => auditQuery.refetch()} />
      ) : null}
      {auditQuery.data ? <AuditTimeline events={auditQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}
