import {
  AlertTriangle,
  BrainCircuit,
  CalendarClock,
  ClipboardList,
  FileText,
  GitBranch,
  HeartPulse,
  History,
  Pill,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react";

type ClinicalNavItem = {
  key: string;
  label: string;
  icon: LucideIcon;
};

type ClinicalNavGroup = {
  title: string;
  items: ClinicalNavItem[];
};

export const clinicalNavGroups: ClinicalNavGroup[] = [
  {
    title: "Ficha",
    items: [
      { key: "ficha", label: "Resumen", icon: ClipboardList },
      { key: "evoluciones", label: "Evoluciones", icon: FileText },
      { key: "encuentros", label: "Encuentros", icon: CalendarClock },
    ],
  },
  {
    title: "Datos",
    items: [
      { key: "eventos", label: "Eventos", icon: GitBranch },
      { key: "problemas", label: "Problemas", icon: ShieldAlert },
      { key: "alergias", label: "Alergias", icon: AlertTriangle },
      { key: "medicacion", label: "Medicamentos", icon: Pill },
      { key: "signos-vitales", label: "Signos vitales", icon: HeartPulse },
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
      { key: "documentos", label: "Documentos", icon: FileText },
      { key: "auditoria", label: "Auditoria", icon: History },
    ],
  },
];

export const clinicalNav = clinicalNavGroups.flatMap((group) => group.items);
