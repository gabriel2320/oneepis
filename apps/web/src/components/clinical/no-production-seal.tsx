"use client";

import { ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export const NO_PRODUCTION_SEAL_TEXT = "Desarrollo / no PHI / no uso clinico real";

export function NoProductionSeal({ className }: { className?: string }) {
  return (
    <Badge
      variant="warning"
      className={cn("max-w-full gap-1 whitespace-normal text-left leading-snug", className)}
      data-no-production-seal="true"
    >
      <ShieldAlert className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      <span>{NO_PRODUCTION_SEAL_TEXT}</span>
    </Badge>
  );
}
