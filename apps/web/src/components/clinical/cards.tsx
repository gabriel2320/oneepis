import type { ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function ClinicalSectionCard({
  title,
  description,
  action,
  children,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="min-w-0 space-y-1">
          <CardTitle className="text-base">{title}</CardTitle>
          {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export function AlertCard({
  title,
  children,
  tone = "warning",
}: {
  title: string;
  children: ReactNode;
  tone?: "warning" | "danger" | "info";
}) {
  const toneClass = {
    warning: "border-warning/40 bg-warning/10 text-warning-foreground",
    danger: "border-destructive/40 bg-destructive/10 text-foreground",
    info: "border-info/40 bg-info/10 text-foreground",
  }[tone];

  return (
    <div className={cn("rounded-md border p-3", toneClass)}>
      <div className="flex items-center gap-2 text-sm font-semibold">
        <AlertTriangle className="h-4 w-4" />
        {title}
      </div>
      <div className="mt-2 text-sm text-muted-foreground">{children}</div>
    </div>
  );
}

export function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <div className="rounded-md border bg-card p-3">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
      {detail ? <p className="mt-1 text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}

export function TimelineCard({ children }: { children: ReactNode }) {
  return <div className="rounded-md border bg-card p-4">{children}</div>;
}

export function PrintableSection({ children }: { children: ReactNode }) {
  return <section className="print-section rounded-md border bg-card p-4">{children}</section>;
}
