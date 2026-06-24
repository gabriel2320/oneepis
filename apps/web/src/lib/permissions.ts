import { DEMO_MODE } from "@/lib/api/client";
import type { AuthUser, UserRole } from "@/lib/types";

const patientWriters: UserRole[] = ["admin", "medico", "dev"];
const medicalWriters: UserRole[] = ["admin", "medico", "dev"];
const vitalSignWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const clinicalEventWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const clinicalRiskWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const preconsultWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const clinicalAiUsers: UserRole[] = ["admin", "medico", "dev"];

export function canCreatePatient(user?: AuthUser | null) {
  return hasAnyRole(user, patientWriters);
}

export function canManagePatient(user?: AuthUser | null) {
  return hasAnyRole(user, patientWriters);
}

export function canManageClinicalEntries(user?: AuthUser | null) {
  return hasAnyRole(user, medicalWriters);
}

export function canManageClinicalEvents(user?: AuthUser | null) {
  return hasAnyRole(user, clinicalEventWriters);
}

export function canManageAllergies(user?: AuthUser | null) {
  return hasAnyRole(user, medicalWriters);
}

export function canManageMedications(user?: AuthUser | null) {
  return hasAnyRole(user, medicalWriters);
}

export function canManageProblems(user?: AuthUser | null) {
  return hasAnyRole(user, medicalWriters);
}

export function canManageEncounters(user?: AuthUser | null) {
  return hasAnyRole(user, medicalWriters);
}

export function canManagePreconsult(user?: AuthUser | null) {
  return hasAnyRole(user, preconsultWriters);
}

export function canManageHospitalDailySheets(user?: AuthUser | null) {
  return hasAnyRole(user, medicalWriters);
}

export function canManageHospitalIndications(user?: AuthUser | null) {
  return hasAnyRole(user, medicalWriters);
}

export function canRecordVitals(user?: AuthUser | null) {
  return hasAnyRole(user, vitalSignWriters);
}

export function canManageClinicalRisks(user?: AuthUser | null) {
  return hasAnyRole(user, clinicalRiskWriters);
}

export function canUseClinicalAi(user?: AuthUser | null) {
  return hasAnyRole(user, clinicalAiUsers);
}

export function hasAnyRole(user: AuthUser | null | undefined, allowedRoles: UserRole[]) {
  if (DEMO_MODE) {
    return true;
  }
  if (!user) {
    return false;
  }
  return user.roles.some((role) => allowedRoles.includes(role));
}
