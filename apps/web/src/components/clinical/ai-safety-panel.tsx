import { ShieldCheck } from "lucide-react";

export function AiSafetyPanel() {
  return (
    <div className="rounded-md border bg-card p-4">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <ShieldCheck className="h-4 w-4 text-success" />
        IA local gobernada
      </div>
      <div className="mt-3 space-y-2 text-sm text-muted-foreground">
        <p>No diagnostica, no firma y no escribe ficha sin confirmacion humana.</p>
        <p>Modelo rapido: llama3.2:latest. Resumen clinico: qwen3:8b si la latencia es aceptable.</p>
      </div>
    </div>
  );
}
