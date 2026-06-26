"use client";

import { Clock, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DEMO_MODE } from "@/lib/api/client";
import type { PatientRecordSnapshot } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ClinicalWorkspaceLayout({
  children,
  aside,
}: {
  children: ReactNode;
  aside?: ReactNode;
}) {
  if (!aside) {
    return <div className="mx-auto max-w-4xl space-y-5">{children}</div>;
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,400px)]">
      <div className="min-w-0 space-y-5">{children}</div>
      <aside className="min-w-0 space-y-4 xl:sticky xl:top-32 xl:self-start" data-print-hidden="true">
        {aside}
      </aside>
    </div>
  );
}

export function FreeTextClinicalEditor({
  label,
  value,
  onChange,
  disabled,
  placeholder,
  minHeightClassName = "min-h-[360px]",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  minHeightClassName?: string;
}) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Textarea
        className={cn("resize-y leading-6", minHeightClassName)}
        disabled={disabled}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

export function PaperLikePanel({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "mx-auto w-full max-w-[820px] rounded-sm border bg-card p-5 shadow-sm md:p-7",
        "relative before:pointer-events-none before:absolute before:inset-x-7 before:top-24 before:border-t before:border-dashed before:border-muted",
        className,
      )}
    >
      <div className="mb-8 flex flex-col gap-2 border-b pb-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
        </div>
        <Badge variant="outline">Borrador</Badge>
      </div>
      {children}
    </section>
  );
}

export function ClinicalSessionFooter({
  record,
  aiAvailable,
}: {
  record: PatientRecordSnapshot;
  aiAvailable?: boolean;
}) {
  const { user, token, isError } = useCurrentUser();
  const renderedAt = new Date().toLocaleString("es-CL", { dateStyle: "short", timeStyle: "short" });
  const sessionLabel = DEMO_MODE
    ? "Demo"
    : !token || isError
      ? "Sin sesion activa"
      : user
        ? user.name
        : "Sesion activa";

  return (
    <footer
      className="mt-8 border-t bg-background/80 px-4 py-3 text-xs text-muted-foreground md:px-6"
      data-print-hidden="true"
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>{sessionLabel}</span>
          <span>Paciente: {record.patient.clinical_identifier ?? record.patient.id}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Clock className="h-3.5 w-3.5" />
          <span suppressHydrationWarning>{renderedAt}</span>
          <Badge variant={aiAvailable ? "safe" : "outline"}>
            {aiAvailable ? "IA disponible" : "IA no disponible"}
          </Badge>
        </div>
      </div>
    </footer>
  );
}

export function UsefulContextCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return <ClinicalSectionCard title={title}>{children}</ClinicalSectionCard>;
}
