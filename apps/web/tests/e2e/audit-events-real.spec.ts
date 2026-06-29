import { expect, test, type Page, type Route } from "@playwright/test";

const patientId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const createdAt = "2026-06-20T10:00:00Z";
const authUser = {
  email: "admin@oneepis.local",
  name: "Admin E2E",
  roles: ["admin", "dev"],
  actor_id: "e2e-admin",
};
const readonlyUser = {
  email: "lector@oneepis.local",
  name: "Lectura E2E",
  roles: ["solo_lectura"],
  actor_id: "e2e-lector",
};

test.skip(
  process.env.NEXT_PUBLIC_DEMO_MODE !== "false",
  "Audit event UI runs in the dedicated non-demo e2e command.",
);

test("patient audit events expose local read/write filters and trace metadata", async ({ page }) => {
  await mockClinicalApi(page);

  await page.goto(`/pacientes/${patientId}/auditoria`);
  const main = page.getByRole("main");

  await expect(main.getByRole("heading", { name: "Auditoria", exact: true })).toBeVisible();
  await expect(main.getByText("Total: 4")).toBeVisible();
  await expect(main.getByText("Lecturas: 2")).toBeVisible();
  await expect(main.getByText("Escrituras: 2")).toBeVisible();

  await expect(main.getByText("patient.read")).toBeVisible();
  await expect(main.getByText("record.read")).toBeVisible();
  await expect(main.getByText("clinical_entry.create")).toBeVisible();
  await expect(main.getByText("patient.update")).toBeVisible();
  await expect(main.getByText("Actor: e2e-medico").first()).toBeVisible();
  await expect(main.getByText(`GET /api/v1/patients/${patientId}`, { exact: true })).toBeVisible();
  await expect(main.getByText(`GET /api/v1/patients/${patientId}/record`)).toBeVisible();
  await expect(main.getByText("corr-patient-1")).toBeVisible();
  await expect(main.getByText("corr-read-1")).toBeVisible();

  await main.getByRole("button", { name: "Lecturas 2" }).click();
  await expect(main.getByText("patient.read")).toBeVisible();
  await expect(main.getByText("record.read")).toBeVisible();
  await expect(main.getByText("clinical_entry.create")).toHaveCount(0);
  await expect(main.getByText(`GET /api/v1/patients/${patientId}`, { exact: true })).toBeVisible();
  await expect(main.getByText(`GET /api/v1/patients/${patientId}/record`)).toBeVisible();
  await expect(main.getByText("corr-patient-1")).toBeVisible();
  await expect(main.getByText("corr-read-1")).toBeVisible();

  await main.getByRole("button", { name: "Escrituras 2" }).click();
  await expect(main.getByText("clinical_entry.create")).toBeVisible();
  await expect(main.getByText("patient.update")).toBeVisible();
  await expect(main.getByText("patient.read")).toHaveCount(0);
  await expect(main.getByText("record.read")).toHaveCount(0);
  await expect(main.getByText(`POST /api/v1/patients/${patientId}/clinical-entries`)).toBeVisible();
  await expect(main.getByText("corr-write-1")).toBeVisible();

  await main.getByRole("button", { name: "Todos 4" }).click();
  await expect(main.getByText("patient.read")).toBeVisible();
  await expect(main.getByText("record.read")).toBeVisible();
  await expect(main.getByText("clinical_entry.create")).toBeVisible();

  await expect(main).not.toContainText(
    /logs seguros|auditoria completa|cumplimiento legal|receta|MAR activo|orden ejecutable/i,
  );
});

test("patient nav hides audit for users without audit_read", async ({ page }) => {
  await mockClinicalApi(page, readonlyUser);

  await page.goto(`/pacientes/${patientId}/ficha`);

  await expect(page.getByRole("heading", { name: /Paciente Auditoria/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "Auditoria" })).toHaveCount(0);
});

async function mockClinicalApi(page: Page, user = authUser) {
  await page.addInitScript(() => {
    window.localStorage.setItem("oneepis.auth.session", "active");
  });
  await page.route("**/api/v1/**", async (route) => {
    await fulfillApi(route, user);
  });
}

async function fulfillApi(route: Route, user: typeof authUser) {
  const request = route.request();
  const url = new URL(request.url());
  const path = url.pathname;
  const origin = request.headers().origin ?? "http://127.0.0.1:3002";
  const corsHeaders = {
    "access-control-allow-origin": origin,
    "access-control-allow-credentials": "true",
    "access-control-allow-methods": "GET,OPTIONS",
    "access-control-allow-headers": "authorization,content-type,x-oneepis-actor,x-oneepis-csrf",
  };

  if (request.method() === "OPTIONS") {
    await route.fulfill({ status: 204, headers: corsHeaders });
    return;
  }
  if (path === "/api/v1/auth/me") {
    await route.fulfill({ json: user, headers: corsHeaders });
    return;
  }
  if (path === "/api/v1/ai/status") {
    await route.fulfill({ json: aiStatus, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/record`) {
    await route.fulfill({ json: patientRecord, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/audit-events`) {
    await route.fulfill({ json: auditEvents, headers: corsHeaders });
    return;
  }
  await route.fulfill({
    status: 404,
    json: { detail: `Unhandled audit test route: ${path}` },
    headers: corsHeaders,
  });
}

const patientRecord = {
  patient: {
    id: patientId,
    first_name: "Paciente",
    last_name: "Auditoria",
    birth_date: "1980-01-01",
    sex_at_birth: "unknown",
    clinical_status: "active",
    current_care_context: "ambulatory",
    clinical_identifier: "AUD-001",
    created_at: createdAt,
    updated_at: createdAt,
  },
  latest_vitals: null,
  active_allergies: [],
  active_medications: [],
  active_problems: [],
  recent_entries: [],
};

const aiStatus = {
  provider: "local_rules",
  enabled: true,
  available: true,
  model: "local_rules",
  summary_model: null,
  suggestions_model: null,
  fallback_model: null,
  embeddings_model: null,
  base_url: null,
  available_models: [],
  tasks: [],
  message: "Reglas locales disponibles.",
};

const auditEvents = [
  {
    id: "10000000-0000-4000-8000-000000000001",
    action: "patient.read",
    entity_type: "Patient",
    entity_id: patientId,
    actor_id: "e2e-medico",
    correlation_id: "corr-patient-1",
    request_method: "GET",
    request_path: `/api/v1/patients/${patientId}`,
    created_at: "2026-06-20T10:15:00Z",
  },
  {
    id: "10000000-0000-4000-8000-000000000002",
    action: "record.read",
    entity_type: "Patient",
    entity_id: patientId,
    actor_id: "e2e-medico",
    correlation_id: "corr-read-1",
    request_method: "GET",
    request_path: `/api/v1/patients/${patientId}/record`,
    created_at: "2026-06-20T10:18:00Z",
  },
  {
    id: "10000000-0000-4000-8000-000000000003",
    action: "clinical_entry.create",
    entity_type: "ClinicalEntry",
    entity_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    actor_id: "e2e-medico",
    correlation_id: "corr-write-1",
    request_method: "POST",
    request_path: `/api/v1/patients/${patientId}/clinical-entries`,
    created_at: "2026-06-20T10:20:00Z",
  },
  {
    id: "10000000-0000-4000-8000-000000000004",
    action: "patient.update",
    entity_type: "Patient",
    entity_id: patientId,
    actor_id: "e2e-medico",
    correlation_id: "corr-write-2",
    request_method: "PATCH",
    request_path: `/api/v1/patients/${patientId}`,
    created_at: "2026-06-20T10:25:00Z",
  },
];
