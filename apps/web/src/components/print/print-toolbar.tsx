"use client";

import { Button } from "@/components/ui/button";

export function PrintToolbar() {
  return (
    <div className="mx-auto mb-4 flex max-w-3xl items-center justify-between gap-3" data-print-hidden="true">
      <div>
        <p className="text-sm font-semibold">Vista papel</p>
        <p className="text-xs text-muted-foreground">Hoja carta con footer de desarrollo.</p>
      </div>
      <Button type="button" onClick={() => window.print()}>
        Imprimir
      </Button>
    </div>
  );
}
