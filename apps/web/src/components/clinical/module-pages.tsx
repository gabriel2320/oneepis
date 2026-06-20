"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Server } from "lucide-react";
import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { TemplateSelector } from "@/components/theme/template-selector";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import {
  AppointmentList,
  BedBoard,
  DailySheet,
  RoundList,
  VisitWorkspace,
} from "@/components/clinical/widgets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAiStatus } from "@/lib/api/ai";
import { API_BASE_URL, DEMO_MODE } from "@/lib/api/client";
import { listActiveHospitalizations } from "@/lib/api/hospitalization";
import { demoEncounters, demoHospitalBeds, demoRecords } from "@/lib/demo-record";
import type { HospitalizationBoardItem } from "@/lib/types";

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

export function HospitalBedsPage() {
  const board = useHospitalizationBoard();

  return (
    <ModulePage title="Camas" description="Tablero hospitalario desde encuentros activos.">
      <ClinicalSectionCard title="Pacientes hospitalizados">
        <HospitalizationBoardContent board={board} />
      </ClinicalSectionCard>
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
  return (
    <ModulePage title="Hoja diaria" description="Pantalla hospitalizada por paciente.">
      <ClinicalSectionCard title="DailySheet">
        <DailySheet />
      </ClinicalSectionCard>
    </ModulePage>
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

export function AmbulatoryHomePage() {
  return (
    <ModulePage
      title="Consulta"
      description="Base para agenda, atencion y resumen longitudinal."
      actions={[{ href: "/consulta/agenda", label: "Agenda" }]}
    >
      <div className="grid gap-4 xl:grid-cols-2">
        <ClinicalSectionCard title="Agenda">
          <AppointmentList />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Atencion">
          <VisitWorkspace />
        </ClinicalSectionCard>
      </div>
    </ModulePage>
  );
}

export function AppointmentPage() {
  return (
    <ModulePage title="Agenda" description="Agenda ambulatoria lista para integracion.">
      <ClinicalSectionCard title="AppointmentList">
        <AppointmentList />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function VisitPage() {
  return (
    <ModulePage title="Atencion" description="Workspace de consulta ambulatoria por paciente.">
      <ClinicalSectionCard title="VisitWorkspace">
        <VisitWorkspace />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function AmbulatorySummaryPage() {
  return (
    <ModulePage title="Resumen ambulatorio" description="Vista longitudinal por paciente.">
      <ClinicalSectionCard title="Resumen">
        <EmptyState title="Resumen pendiente" description="Usara snapshot clinico y evolucion temporal." />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function SettingsHomePage() {
  return (
    <ModulePage
      title="Configuracion"
      description="Apariencia, IA local y contrato API."
      actions={[
        { href: "/configuracion/apariencia", label: "Apariencia" },
        { href: "/configuracion/ia", label: "IA" },
        { href: "/configuracion/api", label: "API" },
      ]}
    >
      <div className="grid gap-4 md:grid-cols-3">
        <ConfigLink href="/configuracion/apariencia" label="Apariencia" />
        <ConfigLink href="/configuracion/ia" label="IA local" />
        <ConfigLink href="/configuracion/api" label="API" />
      </div>
    </ModulePage>
  );
}

export function AppearanceSettingsPage() {
  return (
    <ModulePage title="Apariencia" description="Tema visual persistente por navegador.">
      <ClinicalSectionCard title="Tema">
        <div className="flex flex-wrap items-center gap-3">
          <ThemeToggle />
          <TemplateSelector />
        </div>
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function AiSettingsPage() {
  const aiQuery = useQuery({ queryKey: ["ai-status"], queryFn: getAiStatus });

  return (
    <ModulePage title="IA local" description="Proveedor Ollama desacoplado y seguro.">
      <ClinicalSectionCard title="Estado Ollama">
        {aiQuery.isLoading ? <LoadingRows rows={2} /> : null}
        {aiQuery.isError ? <ErrorState description="No se pudo consultar /ai/status." /> : null}
        {aiQuery.data ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={aiQuery.data.available ? "safe" : "warning"}>
                {aiQuery.data.available ? "Disponible" : "Pendiente"}
              </Badge>
              {aiQuery.data.model ? <Badge variant="outline">{aiQuery.data.model}</Badge> : null}
            </div>
            <p className="text-sm text-muted-foreground">{aiQuery.data.message}</p>
            {aiQuery.data.tasks.length > 0 ? (
              <div className="grid gap-2 md:grid-cols-2">
                {aiQuery.data.tasks.map((task) => (
                  <div key={task.task} className="rounded-md border p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold">{task.task}</p>
                      <Badge variant={task.available ? "safe" : "outline"}>
                        {task.available ? "instalado" : "pendiente"}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{task.model}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function ApiSettingsPage() {
  return (
    <ModulePage title="API" description="Contrato OpenAPI y URL activa del frontend.">
      <ClinicalSectionCard title="Conexion">
        <div className="space-y-3">
          <p className="flex items-center gap-2 text-sm">
            <Server className="h-4 w-4 text-primary" />
            {API_BASE_URL}
          </p>
          <Button asChild variant="outline" size="sm">
            <a href={`${API_BASE_URL}/openapi.json`} target="_blank" rel="noreferrer">
              OpenAPI
            </a>
          </Button>
        </div>
      </ClinicalSectionCard>
    </ModulePage>
  );
}

function ModulePage({
  title,
  description,
  actions = [],
  children,
}: {
  title: string;
  description: string;
  actions?: { href: string; label: string }[];
  children: ReactNode;
}) {
  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-5 p-4 md:p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          </div>
          {actions.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {actions.map((action) => (
                <Button key={action.href} asChild variant="outline" size="sm">
                  <Link href={action.href}>{action.label}</Link>
                </Button>
              ))}
            </div>
          ) : null}
        </div>
        {children}
      </div>
    </AppShell>
  );
}

function ConfigLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="flex items-center justify-between rounded-md border bg-card p-4 text-sm font-semibold transition-colors hover:bg-muted"
    >
      {label}
      <ArrowRight className="h-4 w-4 text-muted-foreground" />
    </Link>
  );
}

function HospitalizationBoardContent({
  board,
}: {
  board: ReturnType<typeof useHospitalizationBoard>;
}) {
  if (board.isLoading) {
    return <LoadingRows rows={3} />;
  }
  if (board.isError) {
    return <ErrorState description="No se pudo cargar el tablero hospitalario." onRetry={board.refetch} />;
  }
  return <BedBoard items={board.items} />;
}

function useHospitalizationBoard() {
  const boardQuery = useQuery({
    queryKey: ["hospitalization-board"],
    queryFn: listActiveHospitalizations,
    enabled: !DEMO_MODE,
  });
  const demoItems = DEMO_MODE ? getDemoHospitalizations() : [];
  return {
    items: DEMO_MODE ? demoItems : (boardQuery.data ?? []),
    isLoading: !DEMO_MODE && boardQuery.isLoading,
    isError: !DEMO_MODE && boardQuery.isError,
    refetch: () => {
      void boardQuery.refetch();
    },
  };
}

function getDemoHospitalizations(): HospitalizationBoardItem[] {
  return demoEncounters
    .filter((encounter) => encounter.type === "hospitalization" && encounter.status === "in_progress")
    .flatMap((encounter) => {
      const record = demoRecords.find((item) => item.patient.id === encounter.patient_id);
      const bed = demoHospitalBeds.find((item) => item.encounter_id === encounter.id) ?? null;
      return record ? [{ patient: record.patient, encounter, bed }] : [];
    });
}
