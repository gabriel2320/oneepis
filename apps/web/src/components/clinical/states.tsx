import type { ReactNode } from "react";
import { AlertCircle, Inbox } from "lucide-react";

import { Button } from "@/components/ui/button";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center rounded-md border border-dashed bg-muted/30 p-6 text-center">
      <Inbox className="h-8 w-8 text-muted-foreground" />
      <p className="mt-3 text-sm font-semibold">{title}</p>
      {description ? <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  title = "No se pudo cargar",
  description,
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4">
      <div className="flex gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
        <div>
          <p className="text-sm font-semibold">{title}</p>
          {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
          {onRetry ? (
            <Button type="button" size="sm" variant="outline" className="mt-3" onClick={onRetry}>
              Reintentar
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function LoadingRows({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-14 animate-pulse rounded-md bg-muted" />
      ))}
    </div>
  );
}
