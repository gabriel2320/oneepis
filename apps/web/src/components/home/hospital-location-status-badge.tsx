import { Badge } from "@/components/ui/badge";
import type {
  HospitalLocationAccessState,
  HospitalLocationStatus,
} from "@/lib/hospital-physical-map";

const statusLabels: Record<HospitalLocationStatus, string> = {
  available: "Disponible",
  available_partial: "Disponible parcial",
  development: "En desarrollo",
  blocked: "Bloqueado",
  future: "Futuro",
};

const accessLabels: Record<HospitalLocationAccessState, string> = {
  available: "Disponible para tu perfil",
  unauthorized: "No autorizado",
  development: "Servicio en desarrollo",
  blocked: "Bloqueado por requisitos clinicos",
  future: "Futuro",
};

export function HospitalLocationStatusBadge({
  status,
  accessState,
}: {
  status: HospitalLocationStatus;
  accessState: HospitalLocationAccessState;
}) {
  const statusVariant = status === "available" || status === "available_partial" ? "safe" : "warning";
  const accessVariant = accessState === "available" ? "safe" : "warning";

  return (
    <div className="flex flex-wrap gap-2">
      <Badge variant={statusVariant}>{statusLabels[status]}</Badge>
      <Badge variant={accessVariant}>{accessLabels[accessState]}</Badge>
    </div>
  );
}

export function hospitalLocationActionText(
  accessState: HospitalLocationAccessState,
  actionLabel: string | undefined,
) {
  if (accessState === "available") return actionLabel ?? "Entrar";
  if (accessState === "unauthorized") return "No autorizado";
  if (accessState === "development") return "En desarrollo";
  if (accessState === "blocked") return "Bloqueado";
  return "Futuro";
}
