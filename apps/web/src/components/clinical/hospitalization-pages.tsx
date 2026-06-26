"use client";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { DomainModulePage } from "@/components/clinical/clinical-domain-module";
import { HospitalCommandCenter } from "@/components/clinical/hospital-command-center";
import { RoundList } from "@/components/clinical/hospitalization-widgets";
import { useHospitalizationBoard } from "@/components/clinical/hospitalization-data";

export function HospitalHomePage() {
  const board = useHospitalizationBoard();

  return (
    <DomainModulePage
      domain="hospital"
      title="Hospitalizacion"
      description="Flujo clasico hospitalario: ingreso, evolucion diaria, indicaciones y epicrisis."
      actions={[
        { href: "/hospitalizacion/camas", label: "Camas" },
        { href: "/hospitalizacion/rondas", label: "Evolucion diaria" },
      ]}
    >
      <HospitalCommandCenter board={board} />
    </DomainModulePage>
  );
}

export function HospitalRoundsPage() {
  const board = useHospitalizationBoard();

  return (
    <DomainModulePage
      domain="hospital"
      title="Evolucion diaria hospitalaria"
      description="Pacientes hospitalizados activos con acceso a ingreso, evolucion diaria, indicaciones y epicrisis."
      actions={[{ href: "/print/hospitalizacion/rondas", label: "Imprimir listado" }]}
    >
      <ClinicalSectionCard
        title="Pacientes hospitalizados"
        description="Cama, ultimo registro diario y accesos al flujo hospitalario clasico."
      >
        <RoundList board={board} />
      </ClinicalSectionCard>
    </DomainModulePage>
  );
}
