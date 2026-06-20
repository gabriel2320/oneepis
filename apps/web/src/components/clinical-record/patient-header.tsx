import { CalendarDays, FileText, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PatientRecordSnapshot } from "@/lib/types";

function getAge(birthDate: string) {
  const birth = new Date(birthDate);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDelta = today.getMonth() - birth.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < birth.getDate())) {
    age -= 1;
  }
  return age;
}

export function PatientHeader({ record }: { record: PatientRecordSnapshot }) {
  const patient = record.patient;

  return (
    <section className="border-b bg-card px-4 py-4 md:px-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="truncate text-xl font-semibold">
              {patient.first_name} {patient.last_name}
            </h1>
            <Badge variant="safe">Ficha activa</Badge>
            <Badge variant="outline">{patient.clinical_identifier}</Badge>
          </div>
          <div className="mt-2 flex flex-wrap gap-3 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <CalendarDays className="h-4 w-4" />
              {getAge(patient.birth_date)} años
            </span>
            <span className="inline-flex items-center gap-1">
              <FileText className="h-4 w-4" />
              {record.recent_entries.length} entradas
            </span>
            <span className="inline-flex items-center gap-1">
              <ShieldCheck className="h-4 w-4" />
              Sin datos reales en demo
            </span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm">
            <FileText className="h-4 w-4" />
            Nueva nota
          </Button>
          <Button size="sm">
            <ShieldCheck className="h-4 w-4" />
            Firmar
          </Button>
        </div>
      </div>
    </section>
  );
}
