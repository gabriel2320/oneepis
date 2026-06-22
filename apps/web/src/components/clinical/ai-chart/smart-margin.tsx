import type { ReactNode } from "react";

export function SmartMarginBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border bg-background p-3 text-xs text-muted-foreground">
      <p className="mb-2 font-medium text-foreground">{title}</p>
      {children}
    </div>
  );
}
