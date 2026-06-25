import type { PaperTraceabilityProps } from "@/components/print/clinical-print-frame";

export function paperTraceability({
  source,
  status,
  actor,
  clinicalDate,
  limitation,
}: {
  source: string;
  status: string;
  actor: string;
  clinicalDate: string;
  limitation: string;
}): PaperTraceabilityProps {
  return {
    items: [
      { label: "Fuente", value: source },
      { label: "Estado", value: status },
      { label: "Actor", value: actor },
      { label: "Fecha clinica", value: clinicalDate },
    ],
    limitation,
  };
}
