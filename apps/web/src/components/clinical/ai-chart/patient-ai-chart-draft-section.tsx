"use client";

import type { HumanReviewConfirmation, SoapDraftState } from "./ai-chart-types";
import { AiChartStep } from "./ai-chart-step";
import { DraftSoapPaper } from "./draft-soap-paper";
import { ErrorState } from "@/components/clinical/states";
import type { DraftSoapFromEventsResponse } from "@/lib/types";

type PatientAiChartDraftSectionProps = {
  draft: DraftSoapFromEventsResponse | null;
  soap: SoapDraftState;
  canWriteSoap: boolean;
  isSaving: boolean;
  saveError: boolean;
  draftError: boolean;
  onSave: (review: HumanReviewConfirmation) => void;
  onSoapChange: (next: SoapDraftState | ((current: SoapDraftState) => SoapDraftState)) => void;
};

export function PatientAiChartDraftSection({
  draft,
  soap,
  canWriteSoap,
  isSaving,
  saveError,
  draftError,
  onSave,
  onSoapChange,
}: PatientAiChartDraftSectionProps) {
  return (
    <>
      {draftError ? <ErrorState description="No se pudo generar el borrador SOAP." /> : null}
      {draft ? (
        <>
          <AiChartStep
            step="4"
            title="Generar borrador SOAP"
            description="El borrador conserva fuentes y margen de revision; no equivale a firma clinica."
          />
          <AiChartStep
            step="5"
            title="Confirmar como borrador no firmado"
            description="La escritura solo ocurre con confirmacion humana y auditoria backend."
          />
          <DraftSoapPaper
            draft={draft}
            soap={soap}
            canWriteSoap={canWriteSoap}
            isSaving={isSaving}
            saveError={saveError}
            onSave={onSave}
            onSoapChange={onSoapChange}
          />
        </>
      ) : null}
    </>
  );
}
