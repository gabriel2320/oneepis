import type { Page, Route } from "@playwright/test";

export type MockAuthUser = {
  email: string;
  name: string;
  roles: string[];
  actor_id: string;
};

export type AmbulatoryVisitMockOptions = {
  authUser: MockAuthUser;
  patientId?: string;
};

const defaultPatientId = "11111111-1111-4111-8111-111111111111";
const createdAt = "2026-06-20T10:00:00Z";

export async function mockAmbulatoryVisitApi(page: Page, options: AmbulatoryVisitMockOptions) {
  const patientId = options.patientId ?? defaultPatientId;
  const { authUser } = options;

  await page.addInitScript(() => {
    window.localStorage.setItem("oneepis.auth.session", "active");
  });

  await page.route("**/api/v1/**", async (route) => {
    await fulfillAmbulatoryVisitApi(route, { authUser, patientId });
  });
}

async function fulfillAmbulatoryVisitApi(
  route: Route,
  context: { authUser: MockAuthUser; patientId: string },
) {
  const request = route.request();
  const url = new URL(request.url());
  const path = url.pathname;
  const origin = request.headers().origin ?? "http://127.0.0.1:3002";
  const corsHeaders = {
    "access-control-allow-origin": origin,
    "access-control-allow-credentials": "true",
    "access-control-allow-methods": "GET,POST,PATCH,OPTIONS",
    "access-control-allow-headers": "authorization,content-type,x-oneepis-actor,x-oneepis-csrf",
  };

  if (request.method() === "OPTIONS") {
    await route.fulfill({ status: 204, headers: corsHeaders });
    return;
  }

  const { authUser, patientId } = context;

  if (path === "/api/v1/auth/me") {
    await route.fulfill({ json: authUser, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/record`) {
    await route.fulfill({ json: buildPatientRecord(patientId), headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/encounters`) {
    await route.fulfill({ json: buildEncounters(patientId), headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/appointments`) {
    await route.fulfill({ json: buildAppointments(patientId), headers: corsHeaders });
    return;
  }

  await route.fulfill({
    status: 404,
    json: { detail: `Unhandled permissions test route: ${path}` },
    headers: corsHeaders,
  });
}

function buildPatientRecord(patientId: string) {
  return {
    patient: {
      id: patientId,
      first_name: "Paciente",
      last_name: "Permisos",
      birth_date: "1984-04-12",
      sex_at_birth: "unknown",
      clinical_status: "active",
      current_care_context: "ambulatory",
      clinical_identifier: "PERM-001",
      created_at: createdAt,
      updated_at: createdAt,
    },
    latest_vitals: null,
    active_allergies: [],
    active_medications: [],
    active_problems: [],
    recent_entries: [
      {
        id: "51111111-1111-4111-8111-111111111111",
        patient_id: patientId,
        encounter_id: "81111111-1111-4111-8111-111111111111",
        kind: "progress",
        status: "signed",
        occurred_at: "2026-06-20T12:15:00Z",
        title: "Control clinico permisos",
        subjective: "Evolucion estable.",
        objective: "Signos dentro de rango demo.",
        assessment: "Sin alertas.",
        plan: "Seguimiento.",
        tags: ["control", "demo"],
        created_by: "profesional.demo",
        created_at: createdAt,
        updated_at: createdAt,
      },
    ],
  };
}

function buildEncounters(patientId: string) {
  return [
    {
      id: "81111111-1111-4111-8111-111111111111",
      patient_id: patientId,
      type: "ambulatory",
      status: "in_progress",
      workflow_kind: "ambulatory_visit",
      reason: "Encuentro permisos",
      started_at: "2026-06-20T12:00:00Z",
      ended_at: null,
      location_label: "Consulta demo",
      notes: "Fixture E2E permisos.",
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

function buildAppointments(patientId: string) {
  return [
    {
      id: "a1111111-1111-4111-8111-111111111111",
      patient_id: patientId,
      starts_at: "2026-06-24T09:00:00Z",
      ends_at: "2026-06-24T09:30:00Z",
      reason: "Control ambulatorio permisos",
      location_label: "Box demo 1",
      clinician_label: "Equipo ambulatorio",
      notes: "Cita ficticia E2E permisos.",
      status: "scheduled",
      created_by: "sistema",
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export { defaultPatientId as ambulatoryPermissionsPatientId };
