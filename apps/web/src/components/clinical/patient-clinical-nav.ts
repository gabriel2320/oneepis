import {
  AlertTriangle,
  BrainCircuit,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  FileText,
  GitBranch,
  HeartPulse,
  History,
  Pill,
  Printer,
  type LucideIcon,
  Stethoscope,
} from "lucide-react";
import type { CareContext } from "@/lib/types";

export type ClinicalNavItem = {
  key: string;
  label: string;
  icon: LucideIcon;
  href?: (patientId: string) => string;
};

export type ClinicalNavGroup = {
  title: string;
  context?: CareContext;
  items: ClinicalNavItem[];
};

export const clinicalNavGroups: ClinicalNavGroup[] = [
  {
    title: "Acciones",
    items: [
      {
        key: "nueva-evolucion",
        label: "Nueva evolucion",
        icon: FileText,
        href: (patientId) => `/pacientes/${patientId}/evoluciones/nueva`,
      },
      {
        key: "receta",
        label: "Receta papel",
        icon: Printer,
        href: (patientId) => `/print/pacientes/${patientId}/receta`,
      },
    ],
  },
  {
    title: "Ficha",
    items: [
      { key: "ficha", label: "Resumen", icon: ClipboardList },
      { key: "evoluciones", label: "Evoluciones", icon: FileText },
      { key: "alergias", label: "Alergias", icon: AlertTriangle },
      { key: "medicacion", label: "Medicamentos", icon: Pill },
      { key: "signos-vitales", label: "Signos vitales", icon: HeartPulse },
    ],
  },
  {
    title: "Hospitalizado",
    context: "hospitalized",
    items: [
      {
        key: "ingreso-hospitalario",
        label: "Ingreso",
        icon: FileText,
        href: (patientId) => `/hospitalizacion/pacientes/${patientId}/ingreso`,
      },
      {
        key: "evolucion-diaria",
        label: "Evolucion diaria",
        icon: ClipboardCheck,
        href: (patientId) => `/hospitalizacion/pacientes/${patientId}/hoja-diaria`,
      },
      {
        key: "indicaciones",
        label: "Indicaciones",
        icon: ClipboardList,
        href: (patientId) => `/hospitalizacion/pacientes/${patientId}/indicaciones`,
      },
      {
        key: "epicrisis",
        label: "Epicrisis",
        icon: FileText,
        href: (patientId) => `/hospitalizacion/pacientes/${patientId}/epicrisis`,
      },
    ],
  },
  {
    title: "Ambulatorio",
    context: "ambulatory",
    items: [
      {
        key: "atencion-ambulatoria",
        label: "Atencion clinica",
        icon: Stethoscope,
        href: (patientId) => `/consulta/pacientes/${patientId}/atencion`,
      },
      {
        key: "resumen-ambulatorio",
        label: "Resumen",
        icon: ClipboardList,
        href: (patientId) => `/consulta/pacientes/${patientId}/resumen`,
      },
      {
        key: "agenda",
        label: "Agenda",
        icon: CalendarDays,
        href: () => "/consulta/agenda",
      },
    ],
  },
  {
    title: "IA",
    items: [
      { key: "ai-chart", label: "AI-Chart", icon: BrainCircuit },
      { key: "ia", label: "IA clinica", icon: BrainCircuit },
    ],
  },
  {
    title: "Control",
    items: [
      { key: "eventos", label: "Eventos", icon: GitBranch },
      { key: "documentos", label: "Documentos", icon: FileText },
      { key: "auditoria", label: "Auditoria", icon: History },
    ],
  },
];

export const clinicalNav = clinicalNavGroups.flatMap((group) => group.items);

export function clinicalNavGroupsForContext(context: CareContext) {
  return clinicalNavGroups.filter((group) => !group.context || group.context === context);
}

export function clinicalNavForContext(context: CareContext) {
  return clinicalNavGroupsForContext(context).flatMap((group) => group.items);
}
