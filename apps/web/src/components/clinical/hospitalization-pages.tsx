"use client";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { HospitalizationBoardContent } from "@/components/clinical/hospital-bed-pages";
import { DailySheet, RoundList } from "@/components/clinical/hospitalization-widgets";
import { useHospitalizationBoard } from "@/components/clinical/hospitalization-data";
import { ModulePage } from "@/components/clinical/module-pages";
import { EmptyState } from "@/components/clinical/states";

export function HospitalHomePage() {
  const board = useHospitalizationBoard();

  return (
    <ModulePage
      title="Hospitalizacion"
      description="Base para camas, rondas, hoja diaria e indicaciones."
      actions={[
        { href: "/hospitalizacion/camas", label: "Camas" },
        { href: "/hospitalizacion/rondas", label: "Rondas" },
      ]}
    >
      <div className="grid gap-4 xl:grid-cols-2">
        <ClinicalSectionCard title="Camas">
          <HospitalizationBoardContent board={board} />
        </ClinicalSectionCard>
        <ClinicalSectionCard title="Rondas">
          <RoundList />
        </ClinicalSectionCard>
      </div>
    </ModulePage>
  );
}

export function HospitalRoundsPage() {
  return (
    <ModulePage title="Rondas" description="Lista de rondas para pacientes hospitalizados.">
      <ClinicalSectionCard title="RoundList">
        <RoundList />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function DailySheetPage() {
  return (
    <ModulePage title="Hoja diaria" description="Pantalla hospitalizada por paciente.">
      <ClinicalSectionCard title="DailySheet">
        <DailySheet />
      </ClinicalSectionCard>
    </ModulePage>
  );
}

export function OrdersPage() {
  return (
    <ModulePage title="Indicaciones" description="Base para indicaciones hospitalarias auditadas.">
      <ClinicalSectionCard title="Indicaciones">
        <EmptyState title="Indicaciones pendientes" description="Requiere permisos y firma clinica." />
      </ClinicalSectionCard>
    </ModulePage>
  );
}
