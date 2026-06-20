import { BrainCircuit, ShieldCheck, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export function AiInsightPanel() {
  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4" />
            IA clínica local
          </CardTitle>
          <Badge variant="warning">Ollama después</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Módulo preparado para asistencia local, con revisión humana obligatoria.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border bg-background p-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <ShieldCheck className="h-4 w-4 text-emerald-700" />
            Guardrails activos
          </div>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>No diagnostica de forma autónoma.</li>
            <li>No envía datos clínicos a terceros.</li>
            <li>No modifica ficha sin confirmación.</li>
          </ul>
        </div>
        <Separator />
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Acciones previstas</p>
          <div className="grid gap-2">
            <Button variant="outline" size="sm" className="justify-start">
              <Sparkles className="h-4 w-4" />
              Resumir evolución
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <Sparkles className="h-4 w-4" />
              Detectar campos incompletos
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <Sparkles className="h-4 w-4" />
              Preparar traspaso clínico
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
