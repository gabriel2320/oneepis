import type { RuleFindingGroup } from "./ai-chart-types";

export function Change24hPanel({ groups }: { groups: RuleFindingGroup[] }) {
  const findings = groups.flatMap((group) =>
    group.items.slice(0, 2).map((item) => ({
      ...item,
      group: group.label,
    })),
  );
  if (findings.length === 0) {
    return null;
  }
  return (
    <div className="mt-4 rounded-md border bg-background p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">Cambios 24 h</p>
        <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">
          reglas estructuradas
        </span>
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-2">
        {findings.map((item) => (
          <div key={`${item.group}-${item.text}`} className="rounded-md border bg-muted/20 p-2 text-xs">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="rounded-md border bg-background px-1.5 py-0.5 text-muted-foreground">
                {item.status}
              </span>
              <span className="font-medium">{item.group}</span>
            </div>
            <p className="mt-1 text-muted-foreground">{item.text}</p>
            <p className="mt-1 text-[11px] text-muted-foreground">Fuente: {item.source}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
