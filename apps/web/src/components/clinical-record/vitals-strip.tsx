import { Activity, HeartPulse, Thermometer, Wind } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import type { PatientRecordSnapshot } from "@/lib/types";

const empty = "Sin registro";

export function VitalsStrip({ record }: { record: PatientRecordSnapshot }) {
  const vitals = record.latest_vitals;
  const items = [
    {
      icon: HeartPulse,
      label: "Presión",
      value: vitals?.systolic_bp ? `${vitals.systolic_bp}/${vitals.diastolic_bp}` : empty,
    },
    {
      icon: Activity,
      label: "Pulso",
      value: vitals?.heart_rate_bpm ? `${vitals.heart_rate_bpm} lpm` : empty,
    },
    {
      icon: Thermometer,
      label: "Temp.",
      value: vitals?.temperature_c ? `${vitals.temperature_c} C` : empty,
    },
    {
      icon: Wind,
      label: "Sat. O2",
      value: vitals?.oxygen_saturation_pct ? `${vitals.oxygen_saturation_pct}%` : empty,
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-accent-foreground">
              <item.icon className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="text-sm font-semibold">{item.value}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
