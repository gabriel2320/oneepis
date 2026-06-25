"use client";

import Link from "next/link";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClinicalEntry, PatientRecordSnapshot } from "@/lib/types";

export function PatientPaperDocuments({
  patientId,
  record,
}: {
  patientId: string;
  record: PatientRecordSnapshot;
}) {
  const entryDocuments = record.recent_entries
    .map((entry) => entryPaperDocument(patientId, entry))
    .filter((item): item is PaperDocument => Boolean(item));
  const documents: PaperDocument[] = [
    {
      id: "ficha",
      title: "Ficha clinica",
      description: "Hoja carta longitudinal desde la ficha del paciente.",
      href: `/print/pacientes/${patientId}/ficha`,
      status: "Generable",
    },
    {
      id: "resumen",
      title: "Resumen paciente",
      description: "Resumen imprimible de desarrollo, no persistido como documento firmado.",
      href: `/print/pacientes/${patientId}/resumen`,
      status: "Generable",
    },
    ...entryDocuments,
  ];

  return (
    <div className="space-y-4">
      <ClinicalSectionCard
        title="Documentos y papel"
        description="Indice de documentos carta disponibles; no gestiona adjuntos externos."
      >
        <div className="grid gap-3 md:grid-cols-2">
          {documents.map((document) => (
            <PaperDocumentCard key={document.id} document={document} />
          ))}
        </div>
      </ClinicalSectionCard>
      <ClinicalSectionCard title="Bloqueados y futuros">
        <div className="grid gap-3 md:grid-cols-3">
          <BlockedDocument label="Receta valida" detail="Requiere firma, folio, actor, fecha clinica y permisos." />
          <BlockedDocument label="Adjuntos externos" detail="Requiere almacenamiento, PHI policy y trazabilidad." />
          <BlockedDocument label="Consentimientos" detail="Requiere firma, custodia y reglas legales." />
        </div>
      </ClinicalSectionCard>
    </div>
  );
}

type PaperDocument = {
  id: string;
  title: string;
  description: string;
  href: string;
  status: string;
  occurredAt?: string;
};

function PaperDocumentCard({ document }: { document: PaperDocument }) {
  return (
    <div className="rounded-md border p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{document.title}</p>
          <p className="mt-1 text-sm text-muted-foreground">{document.description}</p>
          {document.occurredAt ? (
            <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(document.occurredAt)}</p>
          ) : null}
        </div>
        <Badge variant="outline">{document.status}</Badge>
      </div>
      <Button asChild className="mt-3" variant="outline" size="sm">
        <Link href={document.href}>Ver papel</Link>
      </Button>
    </div>
  );
}

function BlockedDocument({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="rounded-md border border-dashed p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{label}</p>
          <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
        </div>
        <Badge variant="warning">Bloqueado</Badge>
      </div>
    </div>
  );
}

function entryPaperDocument(patientId: string, entry: ClinicalEntry): PaperDocument | null {
  if (entry.kind === "progress") {
    return {
      id: entry.id,
      title: entry.title,
      description: "Evolucion clinica imprimible por ID estricto.",
      href: `/print/pacientes/${patientId}/evolucion/${entry.id}`,
      status: entry.status === "signed" ? "Firmada demo" : "Borrador",
      occurredAt: entry.occurred_at,
    };
  }
  if (entry.kind === "intake") {
    return {
      id: entry.id,
      title: entry.title,
      description: "Ingreso medico carta; no equivale a firma legal.",
      href: `/print/hospitalizacion/pacientes/${patientId}/ingreso/${entry.id}`,
      status: entry.status === "signed" ? "Firmada demo" : "Borrador",
      occurredAt: entry.occurred_at,
    };
  }
  if (entry.kind === "discharge_summary") {
    return {
      id: entry.id,
      title: entry.title,
      description: "Epicrisis preliminar carta; no equivale a alta firmada.",
      href: `/print/hospitalizacion/pacientes/${patientId}/epicrisis/${entry.id}`,
      status: entry.status === "signed" ? "Firmada demo" : "Borrador",
      occurredAt: entry.occurred_at,
    };
  }
  return null;
}
