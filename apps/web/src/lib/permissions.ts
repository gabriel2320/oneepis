import { DEMO_MODE } from "@/lib/api/client";
import type {
  HospitalLocationAccessState,
  HospitalPhysicalLocation,
} from "@/lib/hospital-physical-map";
import type { AuthUser, UserRole } from "@/lib/types";

const patientWriters: UserRole[] = ["admin", "medico", "dev"];
const medicalWriters: UserRole[] = ["admin", "medico", "dev"];
const vitalSignWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const clinicalEventWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const clinicalRiskWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const preconsultWriters: UserRole[] = ["admin", "medico", "enfermeria", "dev"];
const clinicalAiUsers: UserRole[] = ["admin", "medico", "dev"];
const patientReaders: UserRole[] = ["admin", "medico", "enfermeria", "solo_lectura", "dev"];

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

export function canReadPatient(user?: AuthUser | null) {
  return hasAnyRole(user, patientReaders);
}

export function hasLocalSession(user?: AuthUser | null) {
  return DEMO_MODE || Boolean(user);
}

export function resolveHospitalLocationAccess(
  location: HospitalPhysicalLocation,
  user?: AuthUser | null,
): HospitalLocationAccessState {
  if (location.status === "future" || location.status === "development" || location.status === "blocked") {
    return location.status;
  }
  if (!location.primaryRoute) {
    return "unauthorized";
  }
  if (location.accessPolicy === "session") {
    return hasLocalSession(user) ? "available" : "unauthorized";
  }
  if (location.accessPolicy === "patient_read") {
    return canReadPatient(user) ? "available" : "unauthorized";
  }
  return "unauthorized";
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
