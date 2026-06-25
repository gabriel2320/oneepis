"use client";

import { useEffect, useState } from "react";
import { BrainCircuit, ShieldCheck, Sparkles } from "lucide-react";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { createClinicalInsight, getAiStatus } from "@/lib/api/ai";
import { DEMO_MODE } from "@/lib/api/client";
import { canUseClinicalAi } from "@/lib/permissions";
import type { AIProviderStatus, ClinicalInsightResponse } from "@/lib/types";

export function AiInsightPanel() {
  const { user } = useCurrentUser();
  const canRequestAi = !DEMO_MODE && canUseClinicalAi(user);
  const [sourceText, setSourceText] = useState(
    "Paciente refiere evolucion estable. Signos vitales sin alertas. Mantener seguimiento.",
  );
  const [status, setStatus] = useState<AIProviderStatus | null>(null);
  const [insight, setInsight] = useState<ClinicalInsightResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canRequestAi) {
      return;
    }
    getAiStatus()
      .then(setStatus)
      .catch(() => {
        setStatus({
          provider: "api",
          enabled: false,
          available: false,
          available_models: [],
          tasks: [],
          message: "API no disponible.",
        });
      });
  }, [canRequestAi]);

  async function handleCreateInsight() {
    if (!canRequestAi) {
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      const response = await createClinicalInsight({
        source_text: sourceText,
        focus: "summary",
      });
      setInsight(response);
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "No se pudo consultar Ollama.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4" />
            IA clinica local
          </CardTitle>
          <Badge variant={status?.available ? "safe" : "warning"}>
            {canRequestAi ? (status?.available ? "Ollama activo" : "Ollama pendiente") : "IA restringida"}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {canRequestAi
            ? (status?.message ?? "Consultando proveedor local...")
            : "El rol actual no permite consultar IA clinica."}
        </p>
        {canRequestAi && status?.tasks?.length ? (
          <div className="flex flex-wrap gap-2">
            {status.tasks.map((task) => (
              <Badge key={task.task} variant={task.available ? "safe" : "outline"}>
                {task.task}: {task.model}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border bg-background p-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <ShieldCheck className="h-4 w-4 text-emerald-700" />
            Guardrails activos
          </div>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>No diagnostica de forma autonoma.</li>
            <li>No envia datos clinicos a terceros.</li>
            <li>No modifica ficha sin confirmacion.</li>
          </ul>
        </div>
        <Separator />
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Texto clinico</p>
          <Textarea
            value={sourceText}
            onChange={(event) => setSourceText(event.target.value)}
            className="min-h-28"
          />
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            disabled={!canRequestAi || isLoading || sourceText.trim().length === 0}
            onClick={handleCreateInsight}
          >
            <Sparkles className="h-4 w-4" />
            {isLoading ? "Generando..." : "Generar borrador local"}
          </Button>
        </div>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {insight ? (
          <div className="space-y-3 rounded-md border bg-background p-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={insight.status === "draft" ? "safe" : "warning"}>
                {insight.status}
              </Badge>
              {insight.model ? <Badge variant="outline">{insight.model}</Badge> : null}
            </div>
            <p className="text-sm">{insight.summary}</p>
            {insight.structured_points.length > 0 ? (
              <ul className="space-y-1 text-sm text-muted-foreground">
                {insight.structured_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            ) : null}
            <Separator />
            <div className="space-y-1 text-xs text-muted-foreground">
              {insight.safety_notes.map((note) => (
                <p key={note}>{note}</p>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
