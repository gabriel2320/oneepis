"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import {
  BedDouble,
  CalendarDays,
  ClipboardList,
  Settings,
  UserRound,
} from "lucide-react";

import { SessionButton } from "@/components/auth/session-button";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { TemplateSelector } from "@/components/theme/template-selector";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/pacientes", label: "Pacientes", icon: UserRound },
  { href: "/hospitalizacion", label: "Hospitalizacion", icon: BedDouble },
  { href: "/consulta", label: "Consulta", icon: CalendarDays },
  { href: "/configuracion", label: "Configuracion", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background">
      <aside
        data-print-hidden="true"
        className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-card lg:block"
      >
        <div className="flex h-full flex-col">
          <div className="border-b p-4">
            <Link href="/pacientes" className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <ClipboardList className="h-5 w-5" />
              </span>
              <span>
                <span className="block text-sm font-semibold">OneEpis</span>
                <span className="block text-xs text-muted-foreground">Paciente / ficha / papel</span>
              </span>
            </Link>
          </div>

          <nav className="flex-1 space-y-1 p-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

              return (
                <Link
                  key={item.href}
                  href={item.href}
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
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <TemplateSelector compact />
            </div>
          </div>
        </div>
      </aside>

      <header
        data-print-hidden="true"
        className="sticky top-0 z-20 border-b bg-card/95 px-4 py-3 backdrop-blur lg:hidden"
      >
        <div className="flex items-center justify-between gap-3">
          <Link href="/pacientes" className="flex items-center gap-2 text-sm font-semibold">
            <ClipboardList className="h-4 w-4" />
            OneEpis
          </Link>
          <div className="flex items-center gap-2">
            <SessionButton compact />
            <ThemeToggle />
            <Button asChild variant="outline" size="sm">
              <Link href="/configuracion/apariencia">Tema</Link>
            </Button>
          </div>
        </div>
        <nav className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
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
      </header>

      <main className="lg:pl-64">{children}</main>
    </div>
  );
}
