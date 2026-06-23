import Link from "next/link";

import { EmptyState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";

export function AppointmentList() {
  return (
    <EmptyState
      title="Agenda ambulatoria"
      description="La agenda persistida vive en su pantalla dedicada."
      action={
        <Button asChild size="sm" variant="outline">
          <Link href="/consulta/agenda">Abrir agenda</Link>
        </Button>
      }
    />
  );
}

export function VisitWorkspace() {
  return (
    <EmptyState
      title="Atencion por paciente"
      description="Encuentro ambulatorio y SOAP vinculada desde ficha paciente."
      action={
        <Button asChild size="sm" variant="outline">
          <Link href="/pacientes">Ver pacientes</Link>
        </Button>
      }
    />
  );
}
