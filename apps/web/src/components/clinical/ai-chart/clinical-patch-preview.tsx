import type { ClinicalPatchOperation } from "@/lib/types";

type ClinicalPatchPreviewProps = {
  operations: ClinicalPatchOperation[];
  paths: string[];
  title?: string;
};

export function ClinicalPatchPreview({
  operations,
  paths,
  title = "Patch clinico",
}: ClinicalPatchPreviewProps) {
  const visibleOperations = operations.filter((operation) => paths.includes(operation.path));
  return (
    <div className="mt-2 rounded-md border bg-muted/30 p-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium text-foreground">{title}</p>
        <span className="rounded-md border bg-background px-1.5 py-0.5">
          {visibleOperations.length} operaciones visibles
        </span>
      </div>
      <ul className="mt-2 space-y-1">
        {visibleOperations.map((operation) => (
          <li key={`${operation.path}-${operation.reason}`} className="grid gap-1 md:grid-cols-[88px_1fr]">
            <span className="font-medium text-foreground">{fieldLabel(operation.path)}</span>
            <span>
              {formatPatchValue(operation.value)}
              <span className="block text-[11px] text-muted-foreground">{operation.reason}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function fieldLabel(path: string) {
  const labels: Record<string, string> = {
    "/event_type": "Tipo",
    "/occurred_at": "Fecha",
    "/summary": "Resumen",
    "/source_type": "Fuente",
    "/title": "Titulo",
    "/subjective": "S",
    "/objective": "O",
    "/assessment": "A",
    "/plan": "P",
  };
  return labels[path] ?? path.replace("/", "");
}

function formatPatchValue(value: unknown) {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (value == null) {
    return "Sin valor";
  }
  return JSON.stringify(value);
}
