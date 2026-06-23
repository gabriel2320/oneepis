"use client";

import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createClinicalRisk, listClinicalRisks, updateClinicalRisk } from "@/lib/api/clinical-risks";
import { DEMO_MODE } from "@/lib/api/client";
import type { ClinicalRisk, ClinicalRiskSeverity, ClinicalRiskType } from "@/lib/types";

const riskTypeLabels: Record<ClinicalRiskType, string> = {
  fall: "Caida",
  pressure_injury: "UPP",
  vte: "TEV",
  isolation: "Aislamiento",
  adverse_event: "Evento adverso",
  other: "Otro",
};

const severityLabels: Record<ClinicalRiskSeverity, string> = {
  low: "Bajo",
  moderate: "Moderado",
  high: "Alto",
  critical: "Critico",
  unknown: "Sin clasificar",
};

export function ClinicalRiskPreview({
  patientId,
  canWrite,
}: {
  patientId: string;
  canWrite: boolean;
}) {
  const queryClient = useQueryClient();
  const [riskType, setRiskType] = useState<ClinicalRiskType>("fall");
  const [severity, setSeverity] = useState<ClinicalRiskSeverity>("unknown");
  const [reason, setReason] = useState("");
  const [humanAction, setHumanAction] = useState("");

  const risksQuery = useQuery({
    queryKey: ["clinical-risks", patientId, "active"],
    queryFn: () => listClinicalRisks(patientId, "active", 10),
    enabled: !DEMO_MODE,
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["clinical-risks", patientId] });

  const createMutation = useMutation({
    mutationFn: () =>
      createClinicalRisk(patientId, {
        risk_type: riskType,
        severity,
        reason: reason.trim(),
        human_action: humanAction.trim() || null,
      }),
    onSuccess: () => {
      setReason("");
      setHumanAction("");
      invalidate();
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (riskId: string) => updateClinicalRisk(patientId, riskId, { status: "resolved" }),
    onSuccess: invalidate,
  });

  const canSubmit = canWrite && !DEMO_MODE && reason.trim().length > 0;

  return (
    <ClinicalSectionCard
      title="Riesgos clinicos"
      description="Registro minimo manual; sin scores automaticos, dashboard ni IA."
    >
      {DEMO_MODE ? (
        <EmptyState
          title="Riesgos disponibles con API real"
          description="La ficha demo no simula seguridad clinica productiva."
        />
      ) : null}
      {risksQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {risksQuery.isError ? (
        <ErrorState
          description="No se pudieron cargar riesgos clinicos."
          onRetry={() => risksQuery.refetch()}
        />
      ) : null}
      {risksQuery.data ? (
        <ClinicalRiskList
          risks={risksQuery.data}
          canWrite={canWrite && !DEMO_MODE}
          onResolve={(riskId) => resolveMutation.mutate(riskId)}
          resolving={resolveMutation.isPending}
        />
      ) : null}
      {canWrite && !DEMO_MODE ? (
        <form
          className="mt-4 space-y-3 border-t pt-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (canSubmit) {
              createMutation.mutate();
            }
          }}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="clinical-risk-type">Tipo</Label>
              <select
                id="clinical-risk-type"
                className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                value={riskType}
                onChange={(event) => setRiskType(event.target.value as ClinicalRiskType)}
              >
                {Object.entries(riskTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="clinical-risk-severity">Severidad</Label>
              <select
                id="clinical-risk-severity"
                className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                value={severity}
                onChange={(event) => setSeverity(event.target.value as ClinicalRiskSeverity)}
              >
                {Object.entries(severityLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="space-y-1">
            <Label htmlFor="clinical-risk-reason">Motivo</Label>
            <Textarea
              id="clinical-risk-reason"
              rows={2}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Ej.: marcha inestable observada durante control."
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="clinical-risk-action">Accion humana</Label>
            <Textarea
              id="clinical-risk-action"
              rows={2}
              value={humanAction}
              onChange={(event) => setHumanAction(event.target.value)}
              placeholder="Ej.: reevaluar en ronda y educar medidas de prevencion."
            />
          </div>
          <Button type="submit" size="sm" disabled={!canSubmit || createMutation.isPending}>
            Registrar riesgo
          </Button>
        </form>
      ) : null}
      <p className="mt-3 text-xs text-muted-foreground">
        Limite visible: 10 riesgos activos. Correcciones se registran por estado; no hay borrado fisico.
      </p>
    </ClinicalSectionCard>
  );
}

function ClinicalRiskList({
  risks,
  canWrite,
  onResolve,
  resolving,
}: {
  risks: ClinicalRisk[];
  canWrite: boolean;
  onResolve: (riskId: string) => void;
  resolving: boolean;
}) {
  if (risks.length === 0) {
    return (
      <EmptyState
        title="Sin riesgos activos"
        description="El registro minimo no calcula scores ni genera alertas automaticas."
      />
    );
  }
  return (
    <div className="space-y-2">
      {risks.map((risk) => (
        <div key={risk.id} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-sm font-medium">{riskTypeLabels[risk.risk_type]}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(risk.created_at)} - Fuente: {risk.source_kind}
              </p>
            </div>
            <Badge variant={risk.severity === "low" ? "safe" : "warning"}>
              {severityLabels[risk.severity]}
            </Badge>
          </div>
          <p className="mt-2 text-sm">{risk.reason}</p>
          {risk.human_action ? (
            <p className="mt-1 text-xs text-muted-foreground">Accion: {risk.human_action}</p>
          ) : null}
          <p className="mt-2 break-all text-[11px] text-muted-foreground">
            Fuente: /api/v1/patients/{risk.patient_id}/clinical-risks/{risk.id}
          </p>
          {canWrite ? (
            <Button
              className="mt-2"
              size="sm"
              variant="outline"
              disabled={resolving}
              onClick={() => onResolve(risk.id)}
            >
              Marcar resuelto
            </Button>
          ) : null}
        </div>
      ))}
    </div>
  );
}
