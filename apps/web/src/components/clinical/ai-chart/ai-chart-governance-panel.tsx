import { ClinicalSectionCard } from "@/components/clinical/cards";

export function AiChartGovernancePanel() {
  return (
    <ClinicalSectionCard title="Gobernanza" description="La IA no firma ni escribe sola.">
      <ul className="space-y-2 text-sm text-muted-foreground">
        <li>Todo borrador requiere revision humana.</li>
        <li>Las fuentes quedan en metadata del borrador.</li>
        <li>Si Ollama esta apagado, se usa degradacion local.</li>
      </ul>
    </ClinicalSectionCard>
  );
}
