"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Search, UserRound } from "lucide-react";

import { AiInsightPanel } from "@/components/clinical-record/ai-insight-panel";
import { ClinicalTimeline } from "@/components/clinical-record/clinical-timeline";
import { NoteEditor } from "@/components/clinical-record/note-editor";
import { PatientHeader } from "@/components/clinical-record/patient-header";
import { VitalsStrip } from "@/components/clinical-record/vitals-strip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { demoRecords } from "@/lib/demo-record";
import { cn } from "@/lib/utils";

export function ClinicalWorkspace() {
  const [activePatientId, setActivePatientId] = useState(demoRecords[0].patient.id);
  const record = useMemo(
    () => demoRecords.find((item) => item.patient.id === activePatientId) ?? demoRecords[0],
    [activePatientId],
  );

  return (
    <main className="flex min-h-screen bg-background">
      <aside className="hidden w-72 shrink-0 border-r bg-card md:block">
        <div className="p-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <UserRound className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold">OneEpis</p>
              <p className="text-xs text-muted-foreground">Ficha clínica</p>
            </div>
          </div>
          <div className="mt-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-9" placeholder="Buscar paciente" />
            </div>
          </div>
        </div>
        <Separator />
        <div className="space-y-2 p-3">
          {demoRecords.map((item) => (
            <button
              key={item.patient.id}
              type="button"
              onClick={() => setActivePatientId(item.patient.id)}
              className={cn(
                "w-full rounded-md border p-3 text-left transition-colors hover:bg-muted",
                item.patient.id === activePatientId && "border-primary bg-accent",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-medium">
                  {item.patient.first_name} {item.patient.last_name}
                </p>
                <Badge variant="outline">{item.patient.clinical_identifier}</Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {item.recent_entries[0]?.title ?? "Sin evolución registrada"}
              </p>
            </button>
          ))}
        </div>
      </aside>

      <section className="min-w-0 flex-1">
        <PatientHeader record={record} />
        <div className="border-b bg-card/70 px-4 py-3 md:hidden">
          <select
            className="h-9 w-full rounded-md border bg-background px-3 text-sm"
            value={activePatientId}
            onChange={(event) => setActivePatientId(event.target.value)}
          >
            {demoRecords.map((item) => (
              <option key={item.patient.id} value={item.patient.id}>
                {item.patient.first_name} {item.patient.last_name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-4 p-4 md:p-6">
          <div className="flex flex-col gap-3 rounded-lg border bg-card p-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-amber-50 text-amber-700">
                <AlertTriangle className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-semibold">Entorno de desarrollo</p>
                <p className="text-sm text-muted-foreground">
                  Datos ficticios. La API ya define persistencia, auditoría y contrato OpenAPI.
                </p>
              </div>
            </div>
            <Button variant="outline" size="sm">
              Ver contrato
            </Button>
          </div>

          <VitalsStrip record={record} />

          <Tabs defaultValue="timeline" className="w-full">
            <TabsList>
              <TabsTrigger value="timeline">Evolución</TabsTrigger>
              <TabsTrigger value="new-entry">Nueva entrada</TabsTrigger>
              <TabsTrigger value="ai">IA</TabsTrigger>
            </TabsList>
            <TabsContent value="timeline">
              <div className="grid gap-4 xl:grid-cols-[1fr_340px]">
                <ClinicalTimeline entries={record.recent_entries} />
                <AiInsightPanel />
              </div>
            </TabsContent>
            <TabsContent value="new-entry">
              <div className="grid gap-4 xl:grid-cols-[1fr_340px]">
                <NoteEditor />
                <AiInsightPanel />
              </div>
            </TabsContent>
            <TabsContent value="ai">
              <div className="max-w-xl">
                <AiInsightPanel />
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </section>
    </main>
  );
}
