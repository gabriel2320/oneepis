"use client";

import {
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import type { AssistantChartSeries } from "@/lib/types";

export function AssistantSeriesChart({ series }: { series: AssistantChartSeries }) {
  const data = series.points.map((point) => ({
    time: new Date(point.occurred_at).toLocaleDateString("es-CL", {
      day: "2-digit",
      month: "2-digit",
    }),
    value: point.value,
  }));
  if (data.length < 2) {
    return null;
  }
  return (
    <div className="mb-3 rounded-md border bg-background p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium">{series.label}</p>
        {series.unit ? <Badge variant="outline">{series.unit}</Badge> : null}
      </div>
      <div className="min-w-0 overflow-x-auto">
        <LineChart width={520} height={160} data={data}>
          <XAxis dataKey="time" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} width={36} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} />
        </LineChart>
      </div>
    </div>
  );
}
