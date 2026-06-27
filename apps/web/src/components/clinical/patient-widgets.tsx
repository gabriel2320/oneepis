"use client";

import Link from "next/link";
import { Activity, AlertTriangle, Sparkles } from "lucide-react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { MetricCard, TimelineCard } from "@/components/clinical/cards";
import { EmptyState } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { careContextLabel, clinicalStatusLabel } from "@/lib/patient-display";
import type {
  ActiveProblem,
  Allergy,
  ClinicalEntry,
  ClinicalEncounter,
  PatientRecordSnapshot,
  VitalSign,
} from "@/lib/types";

import { formatDateTime } from "./date-format";

export { MedicationList } from "@/components/clinical/patient-medication-list";

export function VitalsStrip({ vital }: { vital?: VitalSign | null }) {
  if (!vital) {
    return (
      <div className="grid gap-3 md:grid-cols-4">
        <MetricCard label="PA" value="Sin dato" />
        <MetricCard label="FC" value="Sin dato" />
        <MetricCard label="SatO2" value="Sin dato" />
        <MetricCard label="Temp." value="Sin dato" />
      </div>
    );
  }

  return (
    <div className="grid gap-3 md:grid-cols-4">
      <MetricCard
        label="PA"
        value={
          vital.systolic_bp && vital.diastolic_bp
            ? `${vital.systolic_bp}/${vital.diastolic_bp}`
            : "Sin dato"
        }
        detail={formatDateTime(vital.measured_at)}
      />
      <MetricCard label="FC" value={vital.heart_rate_bpm ? `${vital.heart_rate_bpm}` : "Sin dato"} />
      <MetricCard
        label="SatO2"
        value={vital.oxygen_saturation_pct ? `${vital.oxygen_saturation_pct}%` : "Sin dato"}
      />
      <MetricCard label="Temp." value={vital.temperature_c ? `${vital.temperature_c} C` : "Sin dato"} />
    </div>
  );
}

export function AllergyList({ allergies }: { allergies: Allergy[] }) {
  if (allergies.length === 0) {
    return <EmptyState title="Sin alergias activas" description="No hay alergias registradas." />;
  }

  return (
    <div className="space-y-2">
      {allergies.map((allergy) => (
        <div key={allergy.id} className="flex items-start justify-between gap-3 rounded-md border p-3">
          <div>
            <p className="text-sm font-semibold">{allergy.substance}</p>
            <p className="text-sm text-muted-foreground">{allergy.reaction ?? "Reaccion no documentada"}</p>
          </div>
          <Badge variant={allergy.severity === "severe" ? "warning" : "outline"}>{allergy.severity}</Badge>
        </div>
      ))}
    </div>
  );
}

export function ProblemList({ problems }: { problems: ActiveProblem[] }) {
  if (problems.length === 0) {
    return <EmptyState title="Sin antecedentes activos" description="No hay antecedentes clinicos activos registrados." />;
  }

  return (
    <div className="space-y-2">
      {problems.map((problem) => (
        <div key={problem.id} className="rounded-md border p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">{problem.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {[problem.code_system, problem.code].filter(Boolean).join(" ") || "Sin codigo"}
              </p>
              {problem.notes ? <p className="mt-1 text-xs text-muted-foreground">{problem.notes}</p> : null}
            </div>
            <Badge variant={problem.status === "active" ? "safe" : "outline"}>{problem.status}</Badge>
          </div>
        </div>
      ))}
    </div>
  );
}

export function ClinicalTimeline({ entries }: { entries: ClinicalEntry[] }) {
  if (entries.length === 0) {
    return <EmptyState title="Sin evoluciones" description="Crea una evolucion SOAP para iniciar la ficha." />;
  }

  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <TimelineCard key={entry.id}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">{entry.title}</p>
              <p className="text-xs text-muted-foreground">
                {formatDateTime(entry.occurred_at)} - {entry.created_by}
              </p>
            </div>
            <div className="flex gap-2">
              {entry.encounter_id ? <Badge variant="outline">Atencion vinculada</Badge> : null}
              <Badge variant="outline">{entry.kind}</Badge>
              <Badge variant={entry.status === "signed" ? "safe" : "secondary"}>{entry.status}</Badge>
            </div>
          </div>
          <Separator className="my-3" />
          <div className="grid gap-3 text-sm md:grid-cols-2">
            <SoapBlock label="S" value={entry.subjective} />
            <SoapBlock label="O" value={entry.objective} />
            <SoapBlock label="A" value={entry.assessment} />
            <SoapBlock label="P" value={entry.plan} />
          </div>
        </TimelineCard>
      ))}
    </div>
  );
}

export function EncounterList({ encounters }: { encounters: ClinicalEncounter[] }) {
  if (encounters.length === 0) {
    return <EmptyState title="Sin atenciones vinculadas" description="Crea una consulta, ingreso o atencion inicial." />;
  }

  return (
    <div className="space-y-2">
      {encounters.map((encounter) => (
        <div key={encounter.id} className="rounded-md border p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">{encounter.reason}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {formatDateTime(encounter.started_at)}
                {encounter.location_label ? ` - ${encounter.location_label}` : ""}
              </p>
              {encounter.notes ? <p className="mt-1 text-xs text-muted-foreground">{encounter.notes}</p> : null}
            </div>
            <div className="flex flex-col items-end gap-2">
              <Badge variant="outline">{encounter.type}</Badge>
              <Badge variant={encounter.status === "in_progress" ? "safe" : "secondary"}>
                {encounter.status}
              </Badge>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function CriticalAlerts({ record }: { record: PatientRecordSnapshot }) {
  const severeAllergies = record.active_allergies.filter((item) => item.severity === "severe");

  if (severeAllergies.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border border-warning/50 bg-warning/10 p-3">
      <p className="flex items-center gap-2 text-sm font-semibold">
        <AlertTriangle className="h-4 w-4" />
        Alertas criticas
      </p>
      <p className="mt-1 text-sm text-muted-foreground">
        {severeAllergies.map((item) => item.substance).join(", ")}
      </p>
    </div>
  );
}

export function LatestVitalsTrend({ vitals }: { vitals: VitalSign[] }) {
  const data = vitals
    .slice()
    .reverse()
    .map((vital) => ({
      time: new Date(vital.measured_at).toLocaleTimeString("es-CL", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      fc: vital.heart_rate_bpm ?? null,
      sat: vital.oxygen_saturation_pct ? Number(vital.oxygen_saturation_pct) : null,
    }));

  if (data.length < 2) {
    return <EmptyState title="Tendencia insuficiente" description="Registra al menos dos controles." />;
  }

  return (
    <div className="h-64 rounded-md border p-3">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="time" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} width={32} />
          <Tooltip />
          <Line type="monotone" dataKey="fc" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="sat" stroke="hsl(var(--info))" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PatientLongitudinalSummary({ record }: { record: PatientRecordSnapshot }) {
  const summaryItems = [
    {
      label: "Estado ficha",
      value: clinicalStatusLabel(record.patient.clinical_status),
      detail: careContextLabel(record.patient.current_care_context),
    },
    { label: "Antecedentes", value: `${record.active_problems.length}` },
    { label: "Evoluciones", value: `${record.recent_entries.length}` },
    { label: "Alergias activas", value: `${record.active_allergies.length}` },
    { label: "Medicacion activa", value: `${record.active_medications.length}` },
  ];

  return (
    <div className="rounded-md border bg-muted/20 px-3 py-2">
      <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        {summaryItems.map((item) => (
          <div key={item.label} className="min-w-0">
            <dt className="text-xs font-semibold uppercase text-muted-foreground">{item.label}</dt>
            <dd className="truncate text-sm font-medium text-foreground">{item.value}</dd>
            {item.detail ? (
              <dd className="truncate text-xs text-muted-foreground">{item.detail}</dd>
            ) : null}
          </div>
        ))}
      </dl>
    </div>
  );
}

export function QuickSoapEditor({ href }: { href: string }) {
  return (
    <Button asChild>
      <Link href={href}>
        <Sparkles className="h-4 w-4" />
        Nueva SOAP
      </Link>
    </Button>
  );
}

function SoapBlock({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm">{value || "Sin registro"}</p>
    </div>
  );
}

export function VitalsIcon() {
  return <Activity className="h-4 w-4" />;
}
