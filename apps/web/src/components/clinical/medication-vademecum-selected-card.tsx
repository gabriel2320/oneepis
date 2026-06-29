import { ShieldAlert } from "lucide-react";

import { AddMedicationButton } from "@/components/clinical/medication-vademecum-actions";
import { Badge } from "@/components/ui/badge";
import type { MedicationCatalogItem } from "@/lib/types";

export function SelectedMedicationCard({
  item,
  patientId,
  canWrite,
}: {
  item: MedicationCatalogItem;
  patientId: string;
  canWrite: boolean;
}) {
  const rule = item.dose_rules[0];
  const clinicalUses = item.clinical_uses ?? [];
  const interactionAlerts = item.interaction_alerts ?? [];
  const safetyAlerts = item.safety_alerts ?? [];
  const monitoringNotes = item.monitoring_notes ?? [];
  const routes = item.administration_routes?.length
    ? item.administration_routes
    : item.route
      ? [item.route]
      : [];
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{item.display_name}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Fuente: {item.source_label} / {item.review_status}
          </p>
        </div>
        <Badge variant={item.status === "available" ? "safe" : "outline"}>{item.status}</Badge>
      </div>
      {clinicalUses.length || routes.length ? (
        <div className="mt-3 grid gap-2 text-xs md:grid-cols-2">
          {clinicalUses.length ? (
            <div>
              <p className="font-semibold">Usos curados</p>
              <ul className="mt-1 space-y-1 text-muted-foreground">
                {clinicalUses.slice(0, 2).map((use) => (
                  <li key={`${use.indication}-${use.population ?? "general"}`}>
                    {use.indication}
                    {use.population ? ` / ${use.population}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {routes.length ? (
            <div>
              <p className="font-semibold">Vias</p>
              <p className="mt-1 text-muted-foreground">{routes.join(" / ")}</p>
            </div>
          ) : null}
        </div>
      ) : null}
      {rule ? (
        <div className="mt-3 rounded-md border bg-card p-3 text-xs">
          <p className="flex items-center gap-2 font-semibold">
            <ShieldAlert className="h-4 w-4" />
            Dosis y alertas
          </p>
          <p className="mt-1 text-muted-foreground">
            {rule.usual_dose_text ?? "Dosis usual no curada."}
          </p>
          <p className="mt-1 text-muted-foreground">
            {rule.avoid_dose_text ?? "Dosis a evitar no curada."}
          </p>
          <p className="mt-1 text-muted-foreground">Fuente regla: {rule.source_label}</p>
        </div>
      ) : null}
      {interactionAlerts.length || safetyAlerts.length ? (
        <div className="mt-3 rounded-md border bg-card p-3 text-xs">
          <p className="font-semibold">Alertas informativas</p>
          <ul className="mt-1 space-y-1 text-muted-foreground">
            {interactionAlerts.map((alert) => (
              <li key={`${alert.substance}-${alert.effect}`}>
                Interaccion: {alert.substance} - {alert.effect}
              </li>
            ))}
            {safetyAlerts.map((alert) => (
              <li key={`${alert.title}-${alert.description}`}>
                {alert.title}: {alert.description}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {monitoringNotes.length ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Monitorizacion: {monitoringNotes[0]}
        </p>
      ) : null}
      <AddMedicationButton item={item} patientId={patientId} canWrite={canWrite} />
    </div>
  );
}
