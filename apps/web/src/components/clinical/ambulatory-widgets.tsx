import { EmptyState } from "@/components/clinical/states";

export function AppointmentList() {
  return <EmptyState title="Agenda ambulatoria" description="Agenda lista para integracion posterior." />;
}

export function VisitWorkspace() {
  return <EmptyState title="Atencion ambulatoria" description="Workspace preparado para consulta longitudinal." />;
}
