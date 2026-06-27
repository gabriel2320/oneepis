"use client";

import Link from "next/link";
import { ArrowRight, LayoutList, LockKeyhole, MapPinned } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { DEMO_MODE } from "@/lib/api/client";
import {
  canAccessSection,
  oneEpisSections,
  sectionStatusLabel,
  type OneEpisSection,
} from "@/lib/sections";
import { cn } from "@/lib/utils";

const visibleGroups = [
  "Nucleo paciente",
  "Ambulatorio",
  "Hospitalizacion",
  "Documentos",
  "Configuracion",
] as const;

export function OperationalStartPage() {
  const { user } = useCurrentUser();
  const effectiveUser = DEMO_MODE && !user ? demoOperationalUser : user;

  return (
    <AppShell>
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 md:p-6">
        <header className="flex flex-col gap-4 border-b pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <LayoutList className="h-4 w-4" />
              Inicio operativo
            </div>
            <h1 className="text-2xl font-semibold tracking-normal md:text-3xl">
              Acciones disponibles
            </h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Elige una accion de trabajo segun tu rol. Las acciones bloqueadas
              permanecen visibles solo cuando aclaran un limite clinico o legal.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/home">
              <MapPinned className="h-4 w-4" />
              Ver mapa
            </Link>
          </Button>
        </header>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="space-y-5">
            {visibleGroups.map((group) => {
              const sections = oneEpisSections.filter((section) => section.group === group);
              if (sections.length === 0) return null;

              return (
                <section key={group} className="space-y-2" aria-labelledby={`inicio-${group}`}>
                  <h2 id={`inicio-${group}`} className="text-sm font-semibold">
                    {group}
                  </h2>
                  <div className="overflow-hidden rounded-md border bg-card">
                    {sections.map((section, index) => (
                      <OperationalActionRow
                        key={section.id}
                        section={section}
                        user={effectiveUser}
                        showSeparator={index > 0}
                      />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>

          <aside className="space-y-4">
            <Card className="shadow-none">
              <CardContent className="space-y-3 p-4">
                <div className="space-y-1">
                  <p className="text-sm font-semibold">Contexto de sesion</p>
                  <p className="text-sm text-muted-foreground">
                    {effectiveUser
                      ? `${effectiveUser.name} · sesion autorizada`
                      : "Sesion pendiente de validar"}
                  </p>
                </div>
                <Separator />
                <p className="text-xs leading-5 text-muted-foreground">
                  Esta pantalla no muestra datos clinicos. Para leer o escribir
                  ficha debes entrar por paciente, episodio o documento
                  autorizado.
                </p>
              </CardContent>
            </Card>
          </aside>
        </section>
      </div>
    </AppShell>
  );
}

function OperationalActionRow({
  section,
  user,
  showSeparator,
}: {
  section: OneEpisSection;
  user: Parameters<typeof canAccessSection>[1];
  showSeparator: boolean;
}) {
  const Icon = section.icon;
  const isAvailable = canAccessSection(section, user);
  const status = sectionStatusLabel(section, user);

  return (
    <div className={cn(showSeparator && "border-t")}>
      <div className="grid gap-3 p-3 md:grid-cols-[minmax(0,1fr)_9rem] md:items-center">
        <div className="flex min-w-0 gap-3">
          <span
            className={cn(
              "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md border bg-background text-muted-foreground",
              isAvailable && "border-primary/30 text-primary",
            )}
            aria-hidden="true"
          >
            <Icon className="h-4 w-4" />
          </span>
          <div className="min-w-0 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-medium leading-5">{section.label}</p>
              <Badge variant={isAvailable ? "secondary" : "outline"}>{status}</Badge>
            </div>
            <p className="text-sm leading-6 text-muted-foreground">{section.description}</p>
          </div>
        </div>

        {isAvailable ? (
          <Button asChild className="w-full justify-center" size="sm">
            <Link href={section.href}>
              Entrar
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        ) : (
          <Button className="w-full justify-center" size="sm" variant="outline" disabled>
            <LockKeyhole className="h-4 w-4" />
            No disponible
          </Button>
        )}
      </div>
    </div>
  );
}

const demoOperationalUser = {
  actor_id: "demo",
  email: "demo@oneepis.local",
  name: "Sesion demo",
  roles: ["dev"],
} satisfies NonNullable<Parameters<typeof canAccessSection>[1]>;
