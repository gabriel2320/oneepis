import type { PatientRecordSnapshot } from "@/lib/types";

import { PrintFooter, PrintHeader } from "./clinical-print-frame";

export function PrescriptionA5Sheet({ record }: { record: PatientRecordSnapshot }) {
  return (
    <article className="print-sheet mx-auto min-h-[210mm] max-w-[148mm] border-2 border-warning bg-card p-6 shadow-sm">
      <PrintHeader record={record} title="Receta bloqueada" />
      <div className="space-y-5 py-6">
        <section className="print-section rounded-md border-2 border-warning bg-warning/10 p-4">
          <h2 className="text-sm font-semibold uppercase text-warning-foreground">
            No emitir como receta clinica
          </h2>
          <p className="mt-2 text-sm font-medium">
            Documento bloqueado: no valido para prescribir, dispensar, indicar tratamiento ni
            respaldar compra de medicamentos.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            La prescripcion requiere autenticacion, permisos, validacion clinica, firma profesional
            y politica institucional habilitada.
          </p>
        </section>
        <section className="print-section">
          <h2 className="text-sm font-semibold">Referencia de paciente</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {record.patient.clinical_identifier ?? record.patient.id}
          </p>
        </section>
        <section className="print-section rounded-md border border-dashed p-4">
          <h2 className="text-sm font-semibold">Requisitos no cumplidos</h2>
          <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
            <li>Falta firma profesional habilitada.</li>
            <li>Falta folio institucional verificable.</li>
            <li>Falta actor prescriptor con permisos de receta.</li>
            <li>Falta fecha clinica de emision.</li>
            <li>Falta politica de prescripcion activa.</li>
          </ul>
        </section>
        <section className="print-section min-h-32 border-t pt-4">
          <p className="text-sm font-semibold uppercase">Sin medicamentos autorizados</p>
          <p className="mt-2 text-sm text-muted-foreground">
            OneEpis no imprime recetas mientras el modulo de prescripcion permanezca bloqueado.
          </p>
        </section>
      </div>
      <PrintFooter />
    </article>
  );
}
