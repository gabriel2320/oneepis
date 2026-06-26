import type { ReactNode } from "react";

export function HospitalPhysicalZone({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-3" aria-labelledby={`hospital-zone-${id}`}>
      <h2 id={`hospital-zone-${id}`} className="text-sm font-semibold text-muted-foreground">
        {title}
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{children}</div>
    </section>
  );
}
