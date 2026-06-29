"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BrainCircuit,
  FileText,
  Printer,
  Settings,
  UserRound,
} from "lucide-react";
import type { ReactNode } from "react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { SessionButton } from "@/components/auth/session-button";
import {
  clinicalNavForContext,
  clinicalNavGroupsForContext,
} from "@/components/clinical/patient-clinical-nav";
import { ClinicalSessionFooter } from "@/components/clinical/clinical-workspace";
import { NoProductionSeal } from "@/components/clinical/no-production-seal";
import { ScreenCapabilityBadges } from "@/components/clinical/screen-capability-badges";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { TemplateSelector } from "@/components/theme/template-selector";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAiStatus } from "@/lib/api/ai";
import { careContextLabel, clinicalStatusLabel } from "@/lib/patient-display";
import { canReadAudit } from "@/lib/permissions";
import { findScreenCapability } from "@/lib/screen-capabilities";
import type { PatientRecordSnapshot } from "@/lib/types";
import { cn } from "@/lib/utils";

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
  const router = useRouter();
  const aiStatus = useQuery({ queryKey: ["ai-status"], queryFn: getAiStatus, staleTime: 30_000 });
  const { user } = useCurrentUser();
  const patient = record.patient;
  const relevantAllergy =
    record.active_allergies.find((item) => item.severity === "severe") ??
    record.active_allergies[0];
  const latestEntry = record.recent_entries[0];
  const navGroups = clinicalNavGroupsForContext(patient.current_care_context)
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => item.key !== "auditoria" || canReadAudit(user)),
    }))
    .filter((group) => group.items.length > 0);
  const navItems = clinicalNavForContext(patient.current_care_context).filter(
    (item) => item.key !== "auditoria" || canReadAudit(user),
  );
  const activeNavItem = navItems.find((item) => activeSection === item.key);
  const screenCapability = findScreenCapability(pathname);

  return (
    <div
      className="min-h-screen bg-background"
      data-ai-provider-visible="false"
      data-internal-roles-hidden="true"
      data-workspace="patient"
    >
      <aside
        data-print-hidden="true"
        className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r bg-card lg:block"
      >
        <div className="flex h-full flex-col">
          <div className="border-b p-4">
            <Link href="/home" className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <UserRound className="h-5 w-5" />
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold">OneEpis</span>
                <span className="block truncate text-xs text-muted-foreground">Mapa del hospital</span>
              </span>
            </Link>
          </div>
          <nav aria-label="Navegacion paciente" className="flex-1 space-y-4 overflow-y-auto p-3">
            {navGroups.map((group) => (
              <div key={group.title} className="space-y-1">
                <p className="px-3 text-[11px] font-semibold uppercase text-muted-foreground">
                  {group.title}
                </p>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const href = item.href?.(patient.id) ?? `/pacientes/${patient.id}/${item.key}`;
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
              </div>
            ))}
          </nav>
          <div className="space-y-3 border-t p-3">
            <SessionButton />
            <Button asChild variant="outline" size="sm" className="w-full justify-start">
              <Link href={`/print/pacientes/${patient.id}/ficha`}>
                <Printer className="h-4 w-4" />
                Ver papel / Imprimir
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
                    {clinicalStatusLabel(patient.clinical_status)}
                  </Badge>
                  <Badge variant="outline">{careContextLabel(patient.current_care_context)}</Badge>
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
                <div className="mt-2">
                  <ScreenCapabilityBadges capability={screenCapability} compact />
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <NoProductionSeal />
                <SessionButton compact />
                <Badge variant={aiStatus.data?.available ? "safe" : "warning"}>
                  <BrainCircuit className="mr-1 h-3 w-3" />
                  {aiStatus.data?.available ? "IA local activa" : "IA local pendiente"}
                </Badge>
                <Button asChild size="sm">
                  <Link href={`/pacientes/${patient.id}/evoluciones/nueva`}>
                    <FileText className="h-4 w-4" />
                    Nueva SOAP
                  </Link>
                </Button>
              </div>
            </div>

            <div className="lg:hidden">
              <label htmlFor="patient-section" className="mb-1 block text-xs font-medium text-muted-foreground">
                Seccion clinica
              </label>
              <select
                id="patient-section"
                value={activeNavItem?.key ?? "ficha"}
                className="h-9 w-full rounded-md border bg-background px-3 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                onChange={(event) => {
                  const selectedKey = event.currentTarget.value;
                  const selected = navItems.find((item) => item.key === selectedKey);
                  router.push(selected?.href?.(patient.id) ?? `/pacientes/${patient.id}/${selectedKey}`);
                }}
              >
                {navGroups.map((group) => (
                  <optgroup key={group.title} label={group.title}>
                    {group.items.map((item) => (
                      <option key={item.key} value={item.key}>
                        {item.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-7xl p-4 md:p-6">{children}</main>
        <ClinicalSessionFooter record={record} aiAvailable={aiStatus.data?.available} />
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
