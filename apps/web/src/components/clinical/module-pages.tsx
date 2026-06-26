"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Server } from "lucide-react";
import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { TemplateSelector } from "@/components/theme/template-selector";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { ScreenCapabilityBadges } from "@/components/clinical/screen-capability-badges";
import { ErrorState, LoadingRows } from "@/components/clinical/states";
import { AmbulatoryCommandCenter } from "@/components/clinical/ambulatory-command-center";
import { DomainModulePage } from "@/components/clinical/clinical-domain-module";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getAiStatus } from "@/lib/api/ai";
import { API_BASE_URL } from "@/lib/api/client";
import { findScreenCapability } from "@/lib/screen-capabilities";

export function AmbulatoryHomePage() {
  return (
    <DomainModulePage
      domain="ambulatory"
      title="Consultas ambulatorias"
      description="Flujo ambulatorio centrado en la atencion clinica."
      actions={[{ href: "/consulta/agenda", label: "Agenda" }]}
    >
      <AmbulatoryCommandCenter />
    </DomainModulePage>
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
    <ModulePage title="IA local" description="Proveedor local desacoplado y seguro.">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <ClinicalSectionCard title="Estado IA local">
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
        <ClinicalSectionCard title="IA externa">
          <div className="space-y-3">
            <Badge variant="warning">Bloqueada</Badge>
            <p className="text-sm text-muted-foreground">
              Requiere anonimizar payload, preview humano, autorizacion explicita, auditoria y politica PHI.
            </p>
          </div>
        </ClinicalSectionCard>
      </div>
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

export function ModulePage({
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
  const capability = findScreenCapability(usePathname());
  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-5 p-4 md:p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
            <div className="mt-2">
              <ScreenCapabilityBadges capability={capability} compact />
            </div>
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
