"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  BedDouble,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Home,
  Printer,
  Stethoscope,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";

import { SessionButton } from "@/components/auth/session-button";
import { ClinicalSessionFooter } from "@/components/clinical/clinical-workspace";
import { ScreenCapabilityBadges } from "@/components/clinical/screen-capability-badges";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAiStatus } from "@/lib/api/ai";
import { findScreenCapability } from "@/lib/screen-capabilities";
import type { PatientRecordSnapshot } from "@/lib/types";
import { cn } from "@/lib/utils";

type Domain = "ambulatory" | "hospital";

type DomainNavItem = {
  key: string;
  label: string;
  icon: LucideIcon;
  href: (patientId: string) => string;
};

const ambulatoryNav: DomainNavItem[] = [
  {
    key: "atencion-ambulatoria",
    label: "Atencion clinica",
    icon: Stethoscope,
    href: (patientId) => `/consulta/pacientes/${patientId}/atencion`,
  },
  {
    key: "resumen-ambulatorio",
    label: "Resumen",
    icon: ClipboardList,
    href: (patientId) => `/consulta/pacientes/${patientId}/resumen`,
  },
  {
    key: "agenda",
    label: "Agenda",
    icon: CalendarDays,
    href: () => "/consulta/agenda",
  },
];

const hospitalNav: DomainNavItem[] = [
  {
    key: "ingreso-hospitalario",
    label: "Ingreso",
    icon: FileText,
    href: (patientId) => `/hospitalizacion/pacientes/${patientId}/ingreso`,
  },
  {
    key: "evolucion-diaria",
    label: "Evolucion diaria",
    icon: ClipboardCheck,
    href: (patientId) => `/hospitalizacion/pacientes/${patientId}/hoja-diaria`,
  },
  {
    key: "indicaciones",
    label: "Indicaciones",
    icon: ClipboardList,
    href: (patientId) => `/hospitalizacion/pacientes/${patientId}/indicaciones`,
  },
  {
    key: "epicrisis",
    label: "Epicrisis",
    icon: FileText,
    href: (patientId) => `/hospitalizacion/pacientes/${patientId}/epicrisis`,
  },
];

const domainCopy = {
  ambulatory: {
    title: "Ambulatorio",
    subtitle: "Consulta y seguimiento",
    homeHref: "/consulta",
    homeLabel: "Consultas ambulatorias",
    icon: Stethoscope,
    navLabel: "Navegacion ambulatoria",
  },
  hospital: {
    title: "Hospitalizacion",
    subtitle: "Ingreso y evolucion intrahospitalaria",
    homeHref: "/hospitalizacion",
    homeLabel: "Hospitalizacion",
    icon: BedDouble,
    navLabel: "Navegacion hospitalaria",
  },
} satisfies Record<Domain, {
  title: string;
  subtitle: string;
  homeHref: string;
  homeLabel: string;
  icon: LucideIcon;
  navLabel: string;
}>;

export function AmbulatoryClinicalShell({
  record,
  activeSection,
  children,
}: {
  record: PatientRecordSnapshot;
  activeSection: string;
  children: ReactNode;
}) {
  return (
    <DomainClinicalShell domain="ambulatory" record={record} activeSection={activeSection}>
      {children}
    </DomainClinicalShell>
  );
}

export function HospitalClinicalShell({
  record,
  activeSection,
  children,
}: {
  record: PatientRecordSnapshot;
  activeSection: string;
  children: ReactNode;
}) {
  return (
    <DomainClinicalShell domain="hospital" record={record} activeSection={activeSection}>
      {children}
    </DomainClinicalShell>
  );
}

function DomainClinicalShell({
  domain,
  record,
  activeSection,
  children,
}: {
  domain: Domain;
  record: PatientRecordSnapshot;
  activeSection: string;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const aiStatus = useQuery({ queryKey: ["ai-status"], queryFn: getAiStatus, staleTime: 30_000 });
  const patient = record.patient;
  const copy = domainCopy[domain];
  const navItems = domain === "ambulatory" ? ambulatoryNav : hospitalNav;
  const Icon = copy.icon;
  const screenCapability = findScreenCapability(pathname);
  const activeNavItem = navItems.find((item) => item.key === activeSection);

  return (
    <div className="min-h-screen bg-background">
      <aside
        data-print-hidden="true"
        className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r bg-card lg:block"
      >
        <div className="flex h-full flex-col">
          <div className="border-b p-4">
            <Link href={copy.homeHref} className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <Icon className="h-5 w-5" />
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold">{copy.title}</span>
                <span className="block truncate text-xs text-muted-foreground">{copy.subtitle}</span>
              </span>
            </Link>
          </div>

          <nav aria-label={copy.navLabel} className="flex-1 space-y-1 overflow-y-auto p-3">
            {navItems.map((item) => {
              const ItemIcon = item.icon;
              const href = item.href(patient.id);
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
                  <ItemIcon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="space-y-3 border-t p-3">
            <SessionButton />
            <Button asChild variant="outline" size="sm" className="w-full justify-start">
              <Link href="/home">
                <Home className="h-4 w-4" />
                Mapa del hospital
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="w-full justify-start">
              <Link href={`/pacientes/${patient.id}/ficha`}>
                <ClipboardList className="h-4 w-4" />
                Ficha longitudinal
              </Link>
            </Button>
            <Button asChild variant="ghost" size="sm" className="w-full justify-start">
              <Link href={`/print/pacientes/${patient.id}/ficha`}>
                <Printer className="h-4 w-4" />
                Papel ficha
              </Link>
            </Button>
          </div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header data-print-hidden="true" className="sticky top-0 z-20 border-b bg-card/95 backdrop-blur">
          <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 md:px-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{copy.title}</Badge>
                  <h1 className="truncate text-xl font-semibold">
                    {patient.first_name} {patient.last_name}
                  </h1>
                  {patient.clinical_identifier ? (
                    <Badge variant="outline">{patient.clinical_identifier}</Badge>
                  ) : null}
                </div>
                <div className="mt-2">
                  <ScreenCapabilityBadges capability={screenCapability} compact />
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <SessionButton compact />
                <Badge variant={aiStatus.data?.available ? "safe" : "outline"}>
                  {aiStatus.data?.available ? "IA disponible" : "IA no disponible"}
                </Badge>
                <Button asChild size="sm">
                  <Link href={copy.homeHref}>{copy.homeLabel}</Link>
                </Button>
              </div>
            </div>

            <div className="lg:hidden">
              <label htmlFor="domain-section" className="mb-1 block text-xs font-medium text-muted-foreground">
                Seccion {domain === "ambulatory" ? "ambulatoria" : "hospitalaria"}
              </label>
              <select
                id="domain-section"
                value={activeNavItem?.key ?? navItems[0]?.key}
                className="h-9 w-full rounded-md border bg-background px-3 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                onChange={(event) => {
                  const selected = navItems.find((item) => item.key === event.currentTarget.value);
                  if (selected) router.push(selected.href(patient.id));
                }}
              >
                {navItems.map((item) => (
                  <option key={item.key} value={item.key}>
                    {item.label}
                  </option>
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
