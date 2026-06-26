import { ClinicalSectionCard } from "@/components/clinical/cards";
import { DEMO_MODE } from "@/lib/api/client";

type AiChartGovernancePanelProps = {
  eventCount: number;
  entryCount: number;
  selectedEventCount: number;
  canUseAi: boolean;
  canWriteSoap: boolean;
  canCreateEvents: boolean;
};

export function AiChartGovernancePanel({
  eventCount,
  entryCount,
  selectedEventCount,
  canUseAi,
  canWriteSoap,
  canCreateEvents,
}: AiChartGovernancePanelProps) {
  const soapReady = selectedEventCount > 0 && canUseAi && canWriteSoap && !DEMO_MODE;
  return (
    <ClinicalSectionCard title="Gobernanza" description="La IA no firma ni escribe sola.">
      <div className="space-y-3">
        <div className="rounded-md border bg-muted/30 p-2 text-xs text-muted-foreground">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-medium text-foreground">Estado operativo</p>
            <span className="rounded-md border bg-background px-1.5 py-0.5">
              {soapReady ? "listo para SOAP" : "requiere revision"}
            </span>
          </div>
          <dl className="mt-2 grid grid-cols-2 gap-2">
            <Metric label="Eventos" value={eventCount} />
            <Metric label="Evoluciones" value={entryCount} />
            <Metric label="Seleccionados" value={selectedEventCount} />
            <Metric label="Modo" value={DEMO_MODE ? "demo" : "real"} />
          </dl>
        </div>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>Todo borrador requiere revision humana.</li>
          <li>Las fuentes quedan en metadata del borrador.</li>
          <li>Si la IA local esta apagada, se usa degradacion local.</li>
        </ul>
        <ul className="space-y-1 text-xs text-muted-foreground">
          <li>IA clinica: {canUseAi ? "habilitada" : "requiere perfil autorizado"}</li>
          <li>Guardar SOAP: {canWriteSoap ? "habilitado" : "requiere perfil clinico autorizado"}</li>
          <li>
            Registrar eventos:{" "}
            {canCreateEvents ? "habilitado" : "requiere perfil clinico autorizado"}
          </li>
        </ul>
      </div>
    </ClinicalSectionCard>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd className="font-medium text-foreground">{value}</dd>
    </div>
  );
}
