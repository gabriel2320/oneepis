"use client";

import Link from "next/link";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState } from "@/components/clinical/states";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  canAccessSection,
  oneEpisSections,
  sectionStatusLabel,
  type SectionGroup,
} from "@/lib/sections";

const GROUPS: SectionGroup[] = [
  "Nucleo paciente",
  "Ambulatorio",
  "Hospitalizacion",
  "Documentos",
  "Configuracion",
];

export function SectionsMapPage() {
  const { user, isLoading } = useCurrentUser();

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-5 p-4 md:p-6">
        <div className="rounded-md border bg-card p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase text-muted-foreground">Mapa de secciones</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">OneEpis</h1>
          <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
            Accede solo a las areas habilitadas para tu sesion. Las secciones bloqueadas o en
            desarrollo se muestran sin datos clinicos y no permiten navegacion.
          </p>
        </div>
        {isLoading ? <EmptyState title="Cargando permisos" description="Validando sesion actual." /> : null}
        {GROUPS.map((group) => {
          const sections = oneEpisSections.filter((section) => section.group === group);
          return (
            <ClinicalSectionCard key={group} title={group}>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {sections.map((section) => {
                  const Icon = section.icon;
                  const enabled = canAccessSection(section, user);
                  return (
                    <article key={section.id} className="rounded-md border bg-background p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 items-start gap-3">
                          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted">
                            <Icon className="h-4 w-4" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-sm font-semibold">{section.label}</p>
                            <p className="mt-1 text-xs text-muted-foreground">{section.description}</p>
                          </div>
                        </div>
                        <Badge variant={enabled ? "safe" : "outline"}>
                          {sectionStatusLabel(section, user)}
                        </Badge>
                      </div>
                      <div className="mt-3">
                        {enabled ? (
                          <Button asChild size="sm">
                            <Link href={section.href}>Abrir</Link>
                          </Button>
                        ) : (
                          <Button type="button" size="sm" variant="outline" disabled>
                            No disponible
                          </Button>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            </ClinicalSectionCard>
          );
        })}
      </div>
    </AppShell>
  );
}
