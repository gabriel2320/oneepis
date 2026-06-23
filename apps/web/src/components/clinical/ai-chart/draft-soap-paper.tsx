"use client";

import { useState } from "react";
import { Save } from "lucide-react";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { DEMO_MODE } from "@/lib/api/client";
import type { DraftSoapFromEventsResponse } from "@/lib/types";

import type { HumanReviewConfirmation, SoapDraftState } from "./ai-chart-types";
import { SmartMarginBlock } from "./smart-margin";

type DraftSoapPaperProps = {
  draft: DraftSoapFromEventsResponse;
  soap: SoapDraftState;
  canWriteSoap: boolean;
  isSaving: boolean;
  saveError: boolean;
  onSave: (review: HumanReviewConfirmation) => void;
  onSoapChange: (next: SoapDraftState | ((current: SoapDraftState) => SoapDraftState)) => void;
};

export function DraftSoapPaper({
  draft,
  soap,
  canWriteSoap,
  isSaving,
  saveError,
  onSave,
  onSoapChange,
}: DraftSoapPaperProps) {
  const providerStatus = draft.ai_available ? "IA generativa activa" : "Modo estructurado sin IA";
  const certainty = draft.sources.length > 0 ? "moderada" : "baja";
  const [humanReviewed, setHumanReviewed] = useState(false);
  const saveBlockedReason = soapSaveBlockedReason({ isSaving, canWriteSoap, humanReviewed });
  return (
    <ClinicalSectionCard
      title="Hoja carta SOAP"
      description="Borrador editable con margen inteligente, no firmado."
      action={
        <Button
          type="button"
          size="sm"
          disabled={Boolean(saveBlockedReason)}
          onClick={() =>
            onSave({
              human_reviewed: true,
              human_reviewed_at: new Date().toISOString(),
            })
          }
        >
          <Save className="h-4 w-4" />
          {isSaving ? "Guardando..." : "Guardar borrador"}
        </Button>
      }
    >
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="rounded-md border bg-background p-4 shadow-sm">
          <div className="mb-4 border-b pb-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">
              Evolucion medica · borrador no firmado
            </p>
            <Textarea
              className="mt-2 min-h-16 border-0 bg-muted/30 text-lg font-semibold shadow-none focus-visible:ring-1"
              value={soap.title}
              onChange={(event) =>
                onSoapChange((current) => ({ ...current, title: event.target.value }))
              }
            />
          </div>
          <div className="space-y-4">
            <SoapTextareaLike
              label="S"
              value={soap.subjective}
              onChange={(value) => onSoapChange((current) => ({ ...current, subjective: value }))}
            />
            <SoapTextareaLike
              label="O"
              value={soap.objective}
              onChange={(value) => onSoapChange((current) => ({ ...current, objective: value }))}
            />
            <SoapTextareaLike
              label="A"
              value={soap.assessment}
              onChange={(value) => onSoapChange((current) => ({ ...current, assessment: value }))}
            />
            <SoapTextareaLike
              label="P"
              value={soap.plan}
              onChange={(value) => onSoapChange((current) => ({ ...current, plan: value }))}
            />
          </div>
        </div>
        <aside className="space-y-3 rounded-md border bg-muted/20 p-3">
          <div>
            <p className="text-sm font-medium">Margen inteligente</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Visible, editable y auditable antes de guardar.
            </p>
          </div>
          <SmartMarginBlock title="Estado">
            <p>{providerStatus}</p>
            <p>Proveedor: {draft.provider}</p>
            <p>Certeza: {certainty}</p>
            <p>Firma: requiere confirmacion humana</p>
          </SmartMarginBlock>
          <SmartMarginBlock title="Fuentes">
            {draft.sources.length > 0 ? (
              <ul className="space-y-1">
                {draft.sources.map((source) => (
                  <li key={source.clinical_event_id}>{source.label}</li>
                ))}
              </ul>
            ) : (
              <p>Sin fuentes estructuradas.</p>
            )}
          </SmartMarginBlock>
          <SmartMarginBlock title="Trazabilidad S/O/A/P">
            {draft.section_sources.length > 0 ? (
              <ul className="space-y-2">
                {draft.section_sources.map((source) => (
                  <li key={`${source.section}-${source.source_type}-${source.source_id ?? source.label}`}>
                    <span className="font-medium text-foreground">
                      {soapSectionLabel(source.section)}
                    </span>
                    <span className="block">{source.label}</span>
                    <span className="block">{source.reason}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Sin trazabilidad por seccion.</p>
            )}
          </SmartMarginBlock>
          <SmartMarginBlock title="Datos faltantes y advertencias">
            {draft.warnings.length > 0 ? (
              <ul className="space-y-1">
                {draft.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : (
              <p>Sin advertencias criticas del generador.</p>
            )}
          </SmartMarginBlock>
          <SmartMarginBlock title="Patch de guardado">
            <ul className="space-y-1">
              <li>Titulo: {soap.title || "Sin titulo"}</li>
              <li>S: {sectionState(soap.subjective)}</li>
              <li>O: {sectionState(soap.objective)}</li>
              <li>A: {sectionState(soap.assessment)}</li>
              <li>P: {sectionState(soap.plan)}</li>
            </ul>
            <p className="mt-2">Destino: borrador de evolucion no firmado.</p>
          </SmartMarginBlock>
          {saveBlockedReason && !isSaving ? (
            <SmartMarginBlock title="Bloqueo de guardado">
              <p>{saveBlockedReason}</p>
            </SmartMarginBlock>
          ) : null}
          <SmartMarginBlock title="Acciones humanas">
            <label className="flex gap-2">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={humanReviewed}
                onChange={(event) => setHumanReviewed(event.target.checked)}
              />
              <span>Revise y asumo guardar este texto como borrador clinico.</span>
            </label>
            <ul className="mt-2 space-y-1">
              <li>Editar texto antes de guardar.</li>
              <li>Guardar solo como borrador no firmado.</li>
              <li>Firmar solo en flujo humano futuro.</li>
            </ul>
          </SmartMarginBlock>
          {saveError ? <p className="text-sm text-destructive">No se pudo guardar el borrador.</p> : null}
        </aside>
      </div>
    </ClinicalSectionCard>
  );
}

function SoapTextareaLike({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      {label}
      <Textarea className="min-h-28" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function soapSectionLabel(section: DraftSoapFromEventsResponse["section_sources"][number]["section"]) {
  const labels = {
    subjective: "S",
    objective: "O",
    assessment: "A",
    plan: "P",
  };
  return labels[section];
}

function sectionState(value: string) {
  return value.trim() ? "se guardara texto revisado" : "se guardara vacio";
}

function soapSaveBlockedReason({
  isSaving,
  canWriteSoap,
  humanReviewed,
}: {
  isSaving: boolean;
  canWriteSoap: boolean;
  humanReviewed: boolean;
}) {
  if (isSaving) {
    return "Guardando borrador.";
  }
  if (DEMO_MODE) {
    return "Modo demo: no se guardan borradores reales.";
  }
  if (!canWriteSoap) {
    return "Guardar evoluciones SOAP requiere rol admin, medico o dev.";
  }
  if (!humanReviewed) {
    return "Marca la revision humana antes de guardar.";
  }
  return null;
}
