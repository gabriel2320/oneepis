"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AppointmentCreatePanel } from "@/components/clinical/ambulatory-appointment-create-panel";
import { AppointmentList } from "@/components/clinical/ambulatory-appointment-list";
import { ClinicalSectionCard } from "@/components/clinical/cards";
import { ModulePage } from "@/components/clinical/module-pages";
import { ErrorState, LoadingRows } from "@/components/clinical/states";
import { Input } from "@/components/ui/input";
import { listAppointments } from "@/lib/api/appointments";
import { DEMO_MODE } from "@/lib/api/client";
import { listPatients } from "@/lib/api/patients";
import { demoAppointments, demoRecords } from "@/lib/demo-record";

import { Field } from "./patient-page-shared";

export function AmbulatoryAppointmentPage() {
  const [selectedDate, setSelectedDate] = useState(DEMO_MODE ? "2026-06-24" : todayDate());
  const { start, end } = dayRange(selectedDate);
  const appointmentsQuery = useQuery({
    queryKey: ["appointments", selectedDate],
    queryFn: () => listAppointments(start, end),
    enabled: !DEMO_MODE,
  });
  const patientsQuery = useQuery({
    queryKey: ["patients", "agenda"],
    queryFn: () => listPatients(),
    enabled: !DEMO_MODE,
  });
  const patients = DEMO_MODE ? demoRecords.map((record) => record.patient) : (patientsQuery.data ?? []);
  const appointments = DEMO_MODE
    ? demoAppointments.filter((appointment) => appointment.starts_at.startsWith(selectedDate))
    : (appointmentsQuery.data ?? []);

  return (
    <ModulePage
      title="Agenda"
      description="Agenda ambulatoria persistida, con estados reales y enlace a atencion."
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,420px)]">
        <ClinicalSectionCard title="Agenda ambulatoria" description="Filtra por dia y conserva trazabilidad.">
          <div className="mb-4 max-w-xs">
            <Field label="Dia de agenda">
              <Input
                type="date"
                value={selectedDate}
                onChange={(event) => setSelectedDate(event.target.value)}
              />
            </Field>
          </div>
          {appointmentsQuery.isLoading && !DEMO_MODE ? <LoadingRows rows={3} /> : null}
          {appointmentsQuery.isError && !DEMO_MODE ? (
            <ErrorState description="No se pudo cargar la agenda." onRetry={() => appointmentsQuery.refetch()} />
          ) : null}
          {!appointmentsQuery.isLoading && !appointmentsQuery.isError ? (
            <AppointmentList appointments={appointments} patients={patients} />
          ) : null}
        </ClinicalSectionCard>
        <AppointmentCreatePanel
          patients={patients}
          patientsLoading={patientsQuery.isLoading && !DEMO_MODE}
          selectedDate={selectedDate}
        />
      </div>
    </ModulePage>
  );
}

function todayDate() {
  return new Date().toISOString().slice(0, 10);
}

function dayRange(date: string) {
  return {
    start: new Date(`${date}T00:00:00`).toISOString(),
    end: new Date(`${date}T23:59:59`).toISOString(),
  };
}
