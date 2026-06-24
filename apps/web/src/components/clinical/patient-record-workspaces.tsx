"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { AuditTimeline } from "@/components/clinical/audit-widgets";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import {
  AllergyList,
  EncounterList,
  LatestVitalsTrend,
  MedicationList,
  ProblemList,
  VitalSignList,
  VitalsStrip,
} from "@/components/clinical/patient-widgets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { createPatientAiSuggestions } from "@/lib/api/ai";
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
import type { AuthUser, PatientAiSuggestionsResponse, PatientRecordSnapshot } from "@/lib/types";

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
      title="Encuentros"
      action={
        canWrite ? (
          <Button asChild size="sm">
            <Link href={`/pacientes/${patientId}/encuentros/nuevo`}>Nuevo</Link>
          </Button>
        ) : (
          <NoPermissionButton label="Sin permiso" />
        )
      }
    >
      {encountersQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
      {encountersQuery.isError && !DEMO_MODE ? (
        <ErrorState description="No se pudieron cargar los encuentros." onRetry={() => encountersQuery.refetch()} />
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
    <ClinicalSectionCard
      title="Medicacion"
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
      title="Problemas activos"
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
      <ClinicalSectionCard title="Controles registrados">
        <VitalSignList vitals={vitals} />
      </ClinicalSectionCard>
    </div>
  );
}

export function PatientAiSuggestionsPanel({ patientId, canUseAi }: { patientId: string; canUseAi: boolean }) {
  const suggestionsQuery = useQuery({
    queryKey: ["patient-ai-suggestions", patientId],
    queryFn: () => createPatientAiSuggestions(patientId, { focus: "summary" }),
    enabled: !DEMO_MODE && canUseAi,
    staleTime: 60_000,
  });

  if (DEMO_MODE) {
    return (
      <ClinicalSectionCard title="Sugerencias Ollama" description="Borrador IA - requiere revision humana.">
        <EmptyState title="IA no disponible en demo" description="Usa API real para sugerencias locales." />
      </ClinicalSectionCard>
    );
  }

  if (!canUseAi) {
    return (
      <ClinicalSectionCard title="Sugerencias Ollama" description="Borrador IA - requiere revision humana.">
        <EmptyState
          title="IA no permitida para este rol"
          description="Disponible para medico, admin o dev."
        />
      </ClinicalSectionCard>
    );
  }

  return (
    <ClinicalSectionCard
      title="Sugerencias Ollama"
      description="Borrador IA - requiere revision humana."
      action={
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={suggestionsQuery.isFetching}
          onClick={() => suggestionsQuery.refetch()}
        >
          {suggestionsQuery.isFetching ? "Revisando..." : "Actualizar"}
        </Button>
      }
    >
      {suggestionsQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {suggestionsQuery.isError ? (
        <ErrorState description="No se pudo obtener sugerencias. La ficha sigue operativa." />
      ) : null}
      {suggestionsQuery.data ? <PatientAiSuggestionList response={suggestionsQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function PatientAiSuggestionList({ response }: { response: PatientAiSuggestionsResponse }) {
  return (
    <div className="space-y-3">
      <div className="rounded-md border bg-muted/30 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={response.status === "draft" ? "safe" : "warning"}>{response.status}</Badge>
          <Badge variant="outline">{response.provider}</Badge>
          {response.model ? <Badge variant="outline">{response.model}</Badge> : null}
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{response.summary}</p>
      </div>
      <div className="space-y-2">
        {response.suggestions.map((suggestion) => (
          <div key={`${suggestion.title}-${suggestion.detail}`} className="rounded-md border p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{suggestion.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{suggestion.detail}</p>
              </div>
              <Badge variant={suggestion.severity === "critical" ? "warning" : "outline"}>
                {suggestion.severity}
              </Badge>
            </div>
            {suggestion.action_label ? (
              <p className="mt-2 text-xs text-muted-foreground">{suggestion.action_label}</p>
            ) : null}
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">Borrador IA - requiere revision humana.</p>
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
