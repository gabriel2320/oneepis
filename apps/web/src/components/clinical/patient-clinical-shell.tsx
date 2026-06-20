"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  ClipboardList,
  FileText,
  HeartPulse,
  History,
  Pill,
  Printer,
  Settings,
  ShieldAlert,
  UserRound,
} from "lucide-react";
import type { ReactNode } from "react";

import { SessionButton } from "@/components/auth/session-button";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { TemplateSelector } from "@/components/theme/template-selector";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAiStatus } from "@/lib/api/ai";
import type { PatientRecordSnapshot } from "@/lib/types";
import { cn } from "@/lib/utils";

const clinicalNav = [
  { key: "ficha", label: "Resumen", icon: ClipboardList },
  { key: "evoluciones", label: "Evoluciones", icon: FileText },
  { key: "problemas", label: "Problemas", icon: ShieldAlert },
  { key: "alergias", label: "Alergias", icon: AlertTriangle },
  { key: "medicacion", label: "Medicamentos", icon: Pill },
  { key: "signos-vitales", label: "Signos vitales", icon: HeartPulse },
  { key: "documentos", label: "Documentos", icon: FileText },
  { key: "ia", label: "IA clinica", icon: BrainCircuit },
  { key: "auditoria", label: "Auditoria", icon: History },
] as const;

export function PatientClinicalShell({
  record,
  activeSection,
  children,
}: {
  record: PatientRecordSnapshot;
  activeSection: string;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const aiStatus = useQuery({ queryKey: ["ai-status"], queryFn: getAiStatus, staleTime: 30_000 });
  const patient = record.patient;
  const relevantAllergy =
    record.active_allergies.find((item) => item.severity === "severe") ??
    record.active_allergies[0];
  const latestEntry = record.recent_entries[0];

  return (
    <div className="min-h-screen bg-background">
      <aside
        data-print-hidden="true"
        className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r bg-card lg:block"
      >
        <div className="flex h-full flex-col">
          <div className="border-b p-4">
            <Link href="/pacientes" className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <UserRound className="h-5 w-5" />
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold">OneEpis</span>
                <span className="block truncate text-xs text-muted-foreground">Mesa clinica</span>
              </span>
            </Link>
          </div>
          <nav className="flex-1 space-y-1 p-3">
            {clinicalNav.map((item) => {
              const Icon = item.icon;
              const href = `/pacientes/${patient.id}/${item.key}`;
              const isActive = activeSection === item.key || pathname === href;
              return (
                <Link
                  key={item.key}
                  href={href}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                    isActive && "bg-accent text-accent-foreground",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="space-y-3 border-t p-3">
            <SessionButton />
            <Button asChild variant="outline" size="sm" className="w-full justify-start">
              <Link href={`/print/pacientes/${patient.id}/ficha`}>
                <Printer className="h-4 w-4" />
                Imprimir ficha
              </Link>
            </Button>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <TemplateSelector compact />
            </div>
            <Button asChild variant="ghost" size="sm" className="w-full justify-start">
              <Link href="/configuracion">
                <Settings className="h-4 w-4" />
                Configuracion
              </Link>
            </Button>
          </div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header
          data-print-hidden="true"
          className="sticky top-0 z-20 border-b bg-card/95 backdrop-blur"
        >
          <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 md:px-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="truncate text-xl font-semibold">
                    {patient.first_name} {patient.last_name}
                  </h1>
                  <Badge variant={patient.clinical_status === "active" ? "safe" : "outline"}>
                    {patient.clinical_status}
                  </Badge>
                  <Badge variant="outline">{patient.current_care_context}</Badge>
                  {patient.clinical_identifier ? (
                    <Badge variant="outline">{patient.clinical_identifier}</Badge>
                  ) : null}
                </div>
                <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <span>{ageFromBirthDate(patient.birth_date)}</span>
                  <span>{patient.sex_at_birth}</span>
                  {relevantAllergy ? <span>Alergia: {relevantAllergy.substance}</span> : null}
                  {latestEntry ? <span>Ultima evolucion: {formatShortDate(latestEntry.occurred_at)}</span> : null}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <SessionButton compact />
                <Badge variant={aiStatus.data?.available ? "safe" : "warning"}>
                  <BrainCircuit className="mr-1 h-3 w-3" />
                  {aiStatus.data?.available ? "Ollama activo" : "Ollama pendiente"}
                </Badge>
                <Button asChild size="sm">
                  <Link href={`/pacientes/${patient.id}/evoluciones/nueva`}>
                    <FileText className="h-4 w-4" />
                    Nueva SOAP
                  </Link>
                </Button>
              </div>
            </div>

            <nav className="flex gap-2 overflow-x-auto pb-1 lg:hidden">
              {clinicalNav.map((item) => {
                const href = `/pacientes/${patient.id}/${item.key}`;
                const isActive = activeSection === item.key || pathname === href;
                return (
                  <Link
                    key={item.key}
                    href={href}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground",
                      isActive && "border-primary bg-accent text-accent-foreground",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}

function ageFromBirthDate(value: string) {
  const birthDate = new Date(value);
  if (Number.isNaN(birthDate.getTime())) {
    return "Edad no calculable";
  }
  const now = new Date();
  let age = now.getFullYear() - birthDate.getFullYear();
  const monthDelta = now.getMonth() - birthDate.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && now.getDate() < birthDate.getDate())) {
    age -= 1;
  }
  return `${age} anos`;
}

function formatShortDate(value: string) {
  return new Date(value).toLocaleString("es-CL", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function PatientClinicalLoading() {
  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-3">
        <div className="h-24 animate-pulse rounded-md bg-muted" />
        <div className="grid gap-3 md:grid-cols-3">
          <div className="h-32 animate-pulse rounded-md bg-muted" />
          <div className="h-32 animate-pulse rounded-md bg-muted" />
          <div className="h-32 animate-pulse rounded-md bg-muted" />
        </div>
      </div>
    </div>
  );
}

export function PatientHeaderVitals({ record }: { record: PatientRecordSnapshot }) {
  const vital = record.latest_vitals;
  if (!vital) {
    return <span>Sin signos recientes</span>;
  }
  return (
    <span className="inline-flex items-center gap-1">
      <Activity className="h-3 w-3" />
      FC {vital.heart_rate_bpm ?? "?"} - Sat {vital.oxygen_saturation_pct ?? "?"}
    </span>
  );
}
