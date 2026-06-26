import Link from "next/link";
import type { ReactNode } from "react";
import { CalendarDays, ClipboardList, Stethoscope, UserRound } from "lucide-react";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { Button } from "@/components/ui/button";

export function AmbulatoryCommandCenter() {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <AmbulatoryWorkCard
        icon={<CalendarDays className="h-4 w-4" />}
        title="Agenda ambulatoria"
        description="Citas del dia, estados reales y enlace a la atencion."
        href="/consulta/agenda"
        action="Abrir agenda"
      />
      <AmbulatoryWorkCard
        icon={<UserRound className="h-4 w-4" />}
        title="Seleccionar paciente"
        description="Entrada contextual para abrir una atencion ambulatoria."
        href="/pacientes"
        action="Buscar paciente"
      />
      <AmbulatoryWorkCard
        icon={<Stethoscope className="h-4 w-4" />}
        title="Atencion clinica"
        description="SOAP, preconsulta minima y cierre administrativo auditado."
        href="/pacientes"
        action="Entrar por paciente"
      />
      <section className="lg:col-span-3">
        <ClinicalSectionCard
          title="Limites ambulatorios"
          description="La consulta no activa receta valida, firma legal, orden ejecutable ni admision productiva."
        >
          <div className="grid gap-3 text-sm text-muted-foreground md:grid-cols-3">
            <AmbulatoryLimit label="Preconsulta" value="Minima y autorizada por rol." />
            <AmbulatoryLimit label="Cierre" value="Administrativo y auditable; no firma." />
            <AmbulatoryLimit label="Receta" value="Bloqueada hasta contrato legal." />
          </div>
        </ClinicalSectionCard>
      </section>
    </div>
  );
}

function AmbulatoryWorkCard({
  icon,
  title,
  description,
  href,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  href: string;
  action: string;
}) {
  return (
    <ClinicalSectionCard
      title={title}
      description={description}
      action={<span className="text-primary">{icon}</span>}
    >
      <Button asChild className="w-full justify-center" variant="outline">
        <Link href={href}>
          <ClipboardList className="h-4 w-4" />
          {action}
        </Link>
      </Button>
    </ClinicalSectionCard>
  );
}

function AmbulatoryLimit({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <p className="font-medium text-foreground">{label}</p>
      <p className="mt-1">{value}</p>
    </div>
  );
}
