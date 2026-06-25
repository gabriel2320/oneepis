"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { formatDateTime } from "@/components/clinical/date-format";
import { ClinicalPaperSheet, PrintPage, PrintToolbar } from "@/components/print/clinical-print";
import { DEMO_MODE } from "@/lib/api/client";
import { listHospitalIndications } from "@/lib/api/hospitalization";
import { getPatientRecord } from "@/lib/api/patients";
import { demoHospitalIndications, demoRecords } from "@/lib/demo-record";
import type { HospitalIndication } from "@/lib/types";

import { hospitalIndicationStatusLabel } from "../clinical/hospital-indication-widgets";

export function PrintHospitalIndicationPage() {
  const params = useParams<{ patientId: string; indicationId: string }>();
  const patientId = params.patientId;
  const indicationId = params.indicationId;
  const recordQuery = useQuery({
    queryKey: ["patient-record", patientId],
    queryFn: () => getPatientRecord(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const indicationsQuery = useQuery({
    queryKey: ["hospital-indications", patientId],
    queryFn: () => listHospitalIndications(patientId),
    enabled: Boolean(patientId) && !DEMO_MODE,
  });
  const record =
    (DEMO_MODE ? demoRecords.find((item) => item.patient.id === patientId) ?? demoRecords[0] : null) ??
    recordQuery.data;
  const indications = DEMO_MODE
    ? demoHospitalIndications.filter((item) => item.patient_id === patientId)
    : (indicationsQuery.data ?? []);
  const indication = indications.find((item) => item.id === indicationId) ?? indications[0];

  return (
    <PrintPage>
      <PrintToolbar />
      {record && indication ? (
        <HospitalIndicationPrintSheet indication={indication} record={record} />
      ) : (
        <p className="p-6 text-sm">Cargando indicacion...</p>
      )}
    </PrintPage>
  );
}

function HospitalIndicationPrintSheet({
  record,
  indication,
}: {
  record: Parameters<typeof ClinicalPaperSheet>[0]["record"];
  indication: HospitalIndication;
}) {
  return (
    <ClinicalPaperSheet record={record} title="Indicacion hospitalaria">
      <section className="print-section rounded-md border border-warning/40 bg-warning/10 p-3">
        <h2 className="text-sm font-semibold">
          {indication.status === "closed" ? "Cerrada sin firma legal" : "Borrador no firmado"}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Este documento no equivale a orden ejecutable, firma legal ni receta clinica valida.
        </p>
        <div className="mt-2 grid gap-2 text-xs text-muted-foreground md:grid-cols-2">
          <p>Indicacion: {indication.id}</p>
          <p>Paciente: {indication.patient_id}</p>
          <p>Encuentro: {indication.encounter_id}</p>
          <p>Contexto: {record.patient.current_care_context}</p>
          <p>Fuente: hospital_indications</p>
        </div>
      </section>
      <section className="print-section space-y-3">
        <div>
          <h2 className="text-sm font-semibold">{indication.title}</h2>
          <p className="text-xs text-muted-foreground">
            {formatDateTime(indication.indicated_at)} - {indication.created_by}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Estado: {hospitalIndicationStatusLabel[indication.status]}
          </p>
        </div>
        <PrintTextBlock label="Indicacion" value={indication.indication_text} />
        <PrintTextBlock label="Motivo" value={indication.rationale} />
        <PrintTextBlock label="Seguridad" value={indication.safety_notes} />
      </section>
    </ClinicalPaperSheet>
  );
}

function PrintTextBlock({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-sm">{value || "Sin registro"}</p>
    </div>
  );
}
