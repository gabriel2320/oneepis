"use client";

import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { createPatientAiSuggestions } from "@/lib/api/ai";
import { DEMO_MODE } from "@/lib/api/client";
import type { PatientAiSuggestionsResponse } from "@/lib/types";

export function PatientAiSuggestionsPanel({ patientId, canUseAi }: { patientId: string; canUseAi: boolean }) {
  const suggestionsQuery = useQuery({
    queryKey: ["patient-ai-suggestions", patientId],
    queryFn: () => createPatientAiSuggestions(patientId, { focus: "summary" }),
    enabled: !DEMO_MODE && canUseAi,
    staleTime: 60_000,
  });

  if (DEMO_MODE) {
    return (
      <ClinicalSectionCard title="Apoyo contextual" description="Borrador asistido - requiere revision humana.">
        <EmptyState
          title="Apoyo contextual no disponible en demo"
          description="Usa API real para sugerencias locales."
        />
      </ClinicalSectionCard>
    );
  }

  if (!canUseAi) {
    return (
      <ClinicalSectionCard title="Apoyo contextual" description="Borrador asistido - requiere revision humana.">
        <EmptyState
          title="Apoyo contextual no permitido para este rol"
          description="Disponible para perfiles clinicos autorizados."
        />
      </ClinicalSectionCard>
    );
  }

  return (
    <ClinicalSectionCard
      title="Apoyo contextual"
      description="Borrador asistido - requiere revision humana."
      action={
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={suggestionsQuery.isFetching}
          onClick={() => suggestionsQuery.refetch()}
        >
          {suggestionsQuery.isFetching ? "Revisando..." : "Actualizar"}
        </Button>
      }
    >
      {suggestionsQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {suggestionsQuery.isError ? (
        <ErrorState description="No se pudo obtener sugerencias. La ficha sigue operativa." />
      ) : null}
      {suggestionsQuery.data ? <PatientAiSuggestionList response={suggestionsQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function PatientAiSuggestionList({ response }: { response: PatientAiSuggestionsResponse }) {
  return (
    <div className="space-y-3">
      <div className="rounded-md border bg-muted/30 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={response.status === "draft" ? "safe" : "warning"}>{response.status}</Badge>
          <Badge variant="outline">{response.provider}</Badge>
          {response.model ? <Badge variant="outline">{response.model}</Badge> : null}
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{response.summary}</p>
      </div>
      <div className="space-y-2">
        {response.suggestions.map((suggestion) => (
          <div key={`${suggestion.title}-${suggestion.detail}`} className="rounded-md border p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{suggestion.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{suggestion.detail}</p>
              </div>
              <Badge variant={suggestion.severity === "critical" ? "warning" : "outline"}>
                {suggestion.severity}
              </Badge>
            </div>
            {suggestion.action_label ? (
              <p className="mt-2 text-xs text-muted-foreground">{suggestion.action_label}</p>
            ) : null}
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Borrador asistido - requiere revision humana.
      </p>
    </div>
  );
}
