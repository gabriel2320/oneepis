import { Save, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function NoteEditor() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Nueva entrada SOAP</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-[1fr_160px]">
          <div className="space-y-1.5">
            <Label htmlFor="note-title">Título</Label>
            <Input id="note-title" placeholder="Motivo o contexto del registro" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="note-kind">Tipo</Label>
            <select
              id="note-kind"
              className="h-9 w-full rounded-md border bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              defaultValue="progress"
            >
              <option value="progress">Evolución</option>
              <option value="intake">Ingreso</option>
              <option value="note">Nota</option>
              <option value="procedure">Procedimiento</option>
            </select>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Subjetivo" placeholder="Relato, síntomas, evolución percibida" />
          <Field label="Objetivo" placeholder="Examen, signos, hallazgos verificables" />
          <Field label="Evaluación" placeholder="Impresión clínica documentada" />
          <Field label="Plan" placeholder="Indicaciones, seguimiento, tareas" />
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="outline" size="sm">
            <Sparkles className="h-4 w-4" />
            Ordenar con IA
          </Button>
          <Button size="sm">
            <Save className="h-4 w-4" />
            Guardar borrador
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Field({ label, placeholder }: { label: string; placeholder: string }) {
  const id = `soap-${label.toLowerCase()}`;

  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Textarea id={id} placeholder={placeholder} />
    </div>
  );
}
