"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BedDouble,
  CalendarDays,
  ClipboardList,
  Home,
  Printer,
  Stethoscope,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { ScreenCapabilityBadges } from "@/components/clinical/screen-capability-badges";
import { Button } from "@/components/ui/button";
import { findScreenCapability } from "@/lib/screen-capabilities";
import { cn } from "@/lib/utils";

type Domain = "ambulatory" | "hospital";

type DomainModuleAction = {
  href: string;
  label: string;
};

type DomainModuleNavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const domainConfig = {
  ambulatory: {
    title: "Ambulatorio",
    homeHref: "/consulta",
    icon: Stethoscope,
    nav: [
      { href: "/consulta", label: "Consultas", icon: Stethoscope },
      { href: "/consulta/agenda", label: "Agenda", icon: CalendarDays },
      { href: "/pacientes", label: "Seleccionar paciente", icon: UserRound },
      { href: "/home", label: "Mapa", icon: Home },
    ],
  },
  hospital: {
    title: "Hospitalizacion",
    homeHref: "/hospitalizacion",
    icon: BedDouble,
    nav: [
      { href: "/hospitalizacion", label: "Estacion hospitalaria", icon: BedDouble },
      { href: "/hospitalizacion/rondas", label: "Evolucion diaria", icon: ClipboardList },
      { href: "/hospitalizacion/camas", label: "Camas", icon: BedDouble },
      { href: "/print/hospitalizacion/rondas", label: "Papel de ronda", icon: Printer },
      { href: "/home", label: "Mapa", icon: Home },
    ],
  },
} satisfies Record<Domain, {
  title: string;
  homeHref: string;
  icon: LucideIcon;
  nav: DomainModuleNavItem[];
}>;

export function DomainModulePage({
  domain,
  title,
  description,
  actions = [],
  children,
}: {
  domain: Domain;
  title: string;
  description: string;
  actions?: DomainModuleAction[];
  children: ReactNode;
}) {
  const pathname = usePathname();
  const capability = findScreenCapability(pathname);
  const config = domainConfig[domain];
  const Icon = config.icon;

  return (
    <AppShell>
      <div className="mx-auto flex max-w-7xl flex-col gap-5 p-4 md:p-6">
        <header className="rounded-md border bg-card p-4 md:p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                  <Icon className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    {config.title}
                  </p>
                  <h1 className="truncate text-2xl font-semibold">{title}</h1>
                </div>
              </div>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
                {description}
              </p>
              <div className="mt-3">
                <ScreenCapabilityBadges capability={capability} compact />
              </div>
            </div>
            {actions.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {actions.map((action) => (
                  <Button key={action.href} asChild size="sm" variant="outline">
                    <Link href={action.href}>{action.label}</Link>
                  </Button>
                ))}
              </div>
            ) : null}
          </div>
          <nav aria-label={`Navegacion ${config.title.toLowerCase()}`} className="mt-4 flex gap-2 overflow-x-auto pb-1">
            {config.nav.map((item) => {
              const ItemIcon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex h-9 shrink-0 items-center gap-2 rounded-md border bg-background px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                    isActive && "border-primary/40 bg-accent text-accent-foreground",
                  )}
                >
                  <ItemIcon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </header>
        {children}
      </div>
    </AppShell>
  );
}
