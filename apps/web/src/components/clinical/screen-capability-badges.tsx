import { Badge } from "@/components/ui/badge";
import type { ScreenAiAction, ScreenCapability, ScreenStatus } from "@/lib/screen-capabilities";

type ScreenCapabilityBadgesProps = {
  capability: ScreenCapability | null | undefined;
  compact?: boolean;
};

export function ScreenCapabilityBadges({ capability, compact = false }: ScreenCapabilityBadgesProps) {
  if (!capability) return null;
  const aiActions = uniqueAiActions(capability);
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs" data-screen-capability>
      <Badge variant={statusVariant(capability.status)}>{statusLabel(capability.status)}</Badge>
      {!compact ? <Badge variant="outline">{capability.module}</Badge> : null}
      {capability.writePolicy !== "none" ? (
        <Badge variant="warning">{writeLabel(capability.writePolicy)}</Badge>
      ) : null}
      {capability.paperPolicy !== "none" ? (
        <Badge variant={capability.paperPolicy === "bloqueado" ? "warning" : "outline"}>
          papel {capability.paperPolicy}
        </Badge>
      ) : null}
      {aiActions.length > 0 ? (
        <Badge variant="outline">IA {aiActions.map(aiActionLabel).join(", ")}</Badge>
      ) : null}
    </div>
  );
}

function uniqueAiActions(capability: ScreenCapability) {
  return Array.from(new Set(capability.aiCapabilities.flatMap((item) => item.actions)));
}

function statusVariant(status: ScreenStatus) {
  if (status === "completa" || status === "completa/en expansion gobernada") return "safe";
  if (status === "bloqueada") return "warning";
  return "outline";
}

function statusLabel(status: ScreenStatus) {
  if (status === "completa/en expansion gobernada") return "expansion gobernada";
  return status;
}

function writeLabel(policy: string) {
  if (policy === "clinical_patch") return "ClinicalPatch";
  if (policy === "draft_only") return "borrador";
  if (policy === "patient_write") return "escritura paciente";
  return "escritura";
}

function aiActionLabel(action: ScreenAiAction) {
  const labels: Record<ScreenAiAction, string> = {
    read: "lectura",
    summarize: "resumen",
    search: "busqueda",
    chart: "series",
    validate: "validacion",
    draft: "borrador",
    propose_patch: "patch",
  };
  return labels[action];
}
