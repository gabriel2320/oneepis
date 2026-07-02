"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { VitalSign } from "@/lib/types";

export function LatestVitalsTrendChart({ vitals }: { vitals: VitalSign[] }) {
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
