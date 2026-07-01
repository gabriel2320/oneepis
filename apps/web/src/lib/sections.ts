import type { LucideIcon } from "lucide-react";
import {
  BedDouble,
  CalendarDays,
  ClipboardList,
  FileText,
  Settings,
  ShieldCheck,
  Stethoscope,
  UserRound,
} from "lucide-react";

import {
  canCreatePatient,
  canManageEncounters,
  canReadGlobalClinicalIndex,
  canUseClinicalAi,
  hasAnyRole,
} from "@/lib/permissions";
import type { AuthUser, UserRole } from "@/lib/types";

export type SectionState = "available" | "development" | "blocked" | "disabled";
export type SectionGroup = "Nucleo paciente" | "Ambulatorio" | "Hospitalizacion" | "Documentos" | "Configuracion";
export type SectionPermission =
  | "session"
  | "patient_read"
  | "patient_write"
  | "clinical_write"
  | "global_index"
  | "ai_access";

export type OneEpisSection = {
  id: string;
  label: string;
  href: string;
  group: SectionGroup;
  permission: SectionPermission;
  state: SectionState;
  description: string;
  icon: LucideIcon;
};

export const oneEpisSections: OneEpisSection[] = [
  section("patients", "Pacientes", "/pacientes", "Nucleo paciente", "patient_read", "available", "Mesa interna para seleccionar fichas autorizadas.", UserRound),
  section("new-patient", "Nuevo paciente", "/pacientes/nuevo", "Nucleo paciente", "patient_write", "available", "Registro administrativo minimo para abrir ficha.", ClipboardList),
  section("appointments", "Agenda ambulatoria", "/consulta/agenda", "Ambulatorio", "global_index", "available", "Citas, check-in y enlace a atencion.", CalendarDays),
  section("ambulatory", "Consulta", "/consulta", "Ambulatorio", "patient_read", "available", "Acceso a flujos ambulatorios autorizados.", Stethoscope),
  section("hospitalization", "Hospitalizacion", "/hospitalizacion", "Hospitalizacion", "patient_read", "available", "Ingreso, rondas, camas y documentos hospitalarios.", BedDouble),
  section("hospital-beds", "Camas", "/hospitalizacion/camas", "Hospitalizacion", "clinical_write", "available", "Administracion operativa de camas e ingresos.", BedDouble),
  section("paper", "Documentos y papel", "/pacientes", "Documentos", "patient_read", "available", "Documentos se abren desde la ficha de cada paciente.", FileText),
  section("valid-prescription", "Receta valida", "/print/pacientes/[patientId]/receta", "Documentos", "clinical_write", "blocked", "Requiere firma, folio y politica de prescripcion.", ShieldCheck),
  section("ai-settings", "IA local", "/configuracion/ia", "Configuracion", "ai_access", "available", "Estado de IA local y limites de IA externa.", Settings),
  section("external-ai", "IA externa", "/configuracion/ia", "Configuracion", "ai_access", "blocked", "Bloqueada hasta anonimizar payload y auditar autorizacion.", ShieldCheck),
  section("settings", "Configuracion", "/configuracion", "Configuracion", "session", "available", "Preferencias locales y estado de API.", Settings),
];

export function canAccessSection(sectionItem: OneEpisSection, user: AuthUser | null) {
  if (sectionItem.state !== "available") return false;
  return hasSectionPermission(sectionItem.permission, user);
}

export function sectionStatusLabel(sectionItem: OneEpisSection, user: AuthUser | null) {
  if (sectionItem.state === "blocked") return "Bloqueada";
  if (sectionItem.state === "development") return "En desarrollo";
  if (sectionItem.state === "disabled") return "Deshabilitada";
  return canAccessSection(sectionItem, user) ? "Disponible" : "No autorizado";
}

function section(
  id: string,
  label: string,
  href: string,
  group: SectionGroup,
  permission: SectionPermission,
  state: SectionState,
  description: string,
  icon: LucideIcon,
): OneEpisSection {
  return { id, label, href, group, permission, state, description, icon };
}

function hasSectionPermission(permission: SectionPermission, user: AuthUser | null) {
  if (permission === "session") return Boolean(user);
  if (permission === "patient_read") {
    return hasAnyRole(user, ["admin", "medico", "enfermeria", "solo_lectura", "dev"] satisfies UserRole[]);
  }
  if (permission === "patient_write") return canCreatePatient(user);
  if (permission === "clinical_write") return canManageEncounters(user);
  if (permission === "global_index") return canReadGlobalClinicalIndex(user);
  return canUseClinicalAi(user);
}
