import { expect, test, type Page, type Route } from "@playwright/test";

const patientId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const eventId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const entryId = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
const vitalId = "dddddddd-dddd-4ddd-8ddd-dddddddddddd";
const medicationId = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee";
const labPanelId = "ffffffff-ffff-4fff-8fff-ffffffffffff";
const labResultId = "99999999-9999-4999-8999-999999999999";

test.skip(
  process.env.NEXT_PUBLIC_DEMO_MODE !== "false",
  "Assistant Read real UI runs in the dedicated non-demo e2e command.",
);

test("Assistant Read renders real read-only timeline, search, chart and correlation", async ({
  page,
}) => {
  const calls: string[] = [];
  await mockClinicalApi(page, calls);

  await page.goto(`/pacientes/${patientId}/ai-chart`);

  await expect(page.getByRole("heading", { name: "AI-Chart Core" })).toBeVisible();
  await expect(page.getByText("Assistant Read", { exact: true })).toBeVisible();
  await expect(page.getByText("Assistant Read no disponible en demo")).not.toBeVisible();
  await expect(page.getByText("Solo lectura")).toBeVisible();
  await expect(page.getByText("Fuentes inspeccionables")).toBeVisible();
  await expect(page.getByText("Sin IA externa")).toBeVisible();
  await expect(page.getByText("Control longitudinal real").first()).toBeVisible();
  await expect(page.getByText("Fuente: clinical_entries")).toBeVisible();

  await page.getByRole("tab", { name: /Buscar/ }).click();
  await page.getByPlaceholder("Buscar antecedente, examen o medicamento").fill("metformina");
  await page.getByRole("button", { name: "Buscar" }).click();
  await expect(page.getByText("Metformina iniciada")).toBeVisible();
  await expect(page.getByText("Fuente: medications - Campos: name")).toBeVisible();

  await page.getByRole("tab", { name: /Series/ }).click();
  await expect(page.getByText("Frecuencia cardiaca").first()).toBeVisible();
  await expect(page.getByText("84 lpm").first()).toBeVisible();
  await expect(page.getByText("Limite aplicado: 80")).toBeVisible();
  await expect(page.getByText("Examenes estructurados recientes")).toBeVisible();
  await expect(page.getByText("Perfil renal")).toBeVisible();
  await expect(page.getByText("Creatinina")).toBeVisible();
  await expect(page.getByText("Rango ref.: 0.7-1.3")).toBeVisible();
  await expect(page.getByText(/Estado: active/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir fuente lab_result" })).toBeVisible();

  await page.getByRole("tab", { name: /Correlacion/ }).click();
  await expect(page.getByText("Respiratorio / oxigenacion")).toBeVisible();
  await expect(page.getByText("Sat O2 baja")).toBeVisible();
  await expect(page.getByText(/interpretacion humana/)).toBeVisible();

  await expect(page.getByRole("button", { name: /Guardar|Aceptar|Rechazar/ })).toHaveCount(0);
  expect(calls.some((url) => url.includes("/assistant/timeline"))).toBe(true);
  expect(calls.some((url) => url.includes("/assistant/search"))).toBe(true);
  expect(calls.some((url) => url.includes("/assistant/chart"))).toBe(true);
  expect(calls.some((url) => url.includes("/assistant/correlate"))).toBe(true);
  expect(calls.some((url) => url.includes("/lab-panels"))).toBe(true);
});

async function mockClinicalApi(page: Page, calls: string[]) {
  await page.route("http://127.0.0.1:8000/api/v1/**", async (route) => {
    calls.push(route.request().url());
    await fulfillApi(route);
  });
}

async function fulfillApi(route: Route) {
  const request = route.request();
  const url = new URL(request.url());
  const path = url.pathname;
  const corsHeaders = {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "authorization,content-type,x-oneepis-actor",
  };
  if (request.method() === "OPTIONS") {
    await route.fulfill({ status: 204, headers: corsHeaders });
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
  if (path === `/api/v1/patients/${patientId}/clinical-events`) {
    await route.fulfill({ json: clinicalEvents, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/assistant/timeline`) {
    await route.fulfill({ json: assistantTimeline, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/assistant/search`) {
    await route.fulfill({ json: assistantSearch, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/assistant/chart`) {
    await route.fulfill({ json: assistantChart, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/assistant/correlate`) {
    await route.fulfill({ json: assistantCorrelation, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/lab-panels`) {
    await route.fulfill({ json: labPanels, headers: corsHeaders });
    return;
  }
  await route.fulfill({
    status: 404,
    json: { detail: `Unhandled test route: ${path}` },
    headers: corsHeaders,
  });
}

const createdAt = "2026-06-20T10:00:00Z";

const patient = {
  id: patientId,
  first_name: "Paciente",
  last_name: "Assistant",
  birth_date: "1980-01-01",
  sex_at_birth: "unknown",
  clinical_status: "active",
  current_care_context: "ambulatory",
  clinical_identifier: "AR-001",
  created_at: createdAt,
  updated_at: createdAt,
};

const recentEntry = {
  id: entryId,
  patient_id: patientId,
  encounter_id: null,
  kind: "progress",
  status: "draft",
  occurred_at: "2026-06-20T10:10:00Z",
  title: "Control longitudinal real",
  subjective: "Paciente refiere disnea leve.",
  objective: "Sat O2 91%.",
  assessment: "Requiere seguimiento.",
  plan: "Control y revisar fuentes.",
  tags: ["assistant-read"],
  created_by: "playwright.dev",
  created_at: createdAt,
  updated_at: createdAt,
};

const patientRecord = {
  patient,
  latest_vitals: null,
  active_allergies: [],
  active_medications: [],
  active_problems: [],
  recent_entries: [recentEntry],
};

const clinicalEvents = [
  {
    id: eventId,
    patient_id: patientId,
    encounter_id: null,
    event_type: "clinical_note",
    occurred_at: "2026-06-20T10:20:00Z",
    summary: "Disnea y saturacion baja",
    source_type: "manual",
    source_ref: null,
    payload: {},
    created_by: "playwright.dev",
    created_at: createdAt,
    updated_at: createdAt,
  },
];

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

const assistantTimeline = {
  patient_id: patientId,
  items: [
    {
      item_type: "clinical_entry",
      item_id: entryId,
      occurred_at: "2026-06-20T10:10:00Z",
      label: "Control longitudinal real",
      summary: "Paciente refiere disnea leve.",
      source_label: "clinical_entries",
      source_path: `/api/v1/patients/${patientId}/clinical-entries/${entryId}`,
    },
  ],
  missing_data: [],
  warnings: [],
  limit: 20,
  has_more: false,
  applies_changes: false,
};

const assistantSearch = {
  patient_id: patientId,
  query: "metformina",
  results: [
    {
      item_type: "medication",
      item_id: medicationId,
      occurred_at: "2026-06-19T08:00:00Z",
      label: "Metformina",
      snippet: "Metformina iniciada 850 mg.",
      matched_fields: ["name"],
      source_label: "medications",
      source_path: `/api/v1/patients/${patientId}/medications/${medicationId}`,
    },
  ],
  missing_data: [],
  warnings: [],
  limit: 20,
  has_more: false,
  applies_changes: false,
};

const assistantChart = {
  patient_id: patientId,
  series: [
    {
      key: "heart_rate_bpm",
      label: "Frecuencia cardiaca",
      unit: "lpm",
      source_label: "vital_signs",
      points: [
        {
          occurred_at: "2026-06-20T09:00:00Z",
          value: 76,
          source_type: "vital_sign",
          source_id: vitalId,
          source_path: `/api/v1/patients/${patientId}/vital-signs/${vitalId}`,
          note: null,
        },
        {
          occurred_at: "2026-06-20T10:00:00Z",
          value: 84,
          source_type: "vital_sign",
          source_id: vitalId,
          source_path: `/api/v1/patients/${patientId}/vital-signs/${vitalId}`,
          note: null,
        },
      ],
    },
  ],
  missing_data: [],
  warnings: [],
  limit: 80,
  has_more: false,
  applies_changes: false,
};

const assistantCorrelation = {
  patient_id: patientId,
  correlations: [
    {
      preset: "respiratory_oxygen",
      label: "Respiratorio / oxigenacion",
      summary: "Saturacion baja y disnea requieren interpretacion humana.",
      evidence: [
        {
          source_type: "vital_sign",
          source_id: vitalId,
          occurred_at: "2026-06-20T10:00:00Z",
          label: "Sat O2 baja",
          summary: "Saturacion 91%.",
          source_path: `/api/v1/patients/${patientId}/vital-signs/${vitalId}`,
        },
      ],
      missing_data: [],
      warnings: [],
    },
  ],
  missing_data: [],
  warnings: [],
  limit: 80,
  has_more: false,
  applies_changes: false,
};

const labPanels = [
  {
    id: labPanelId,
    patient_id: patientId,
    encounter_id: null,
    occurred_at: "2026-06-20T08:30:00Z",
    panel_name: "Perfil renal",
    source_type: "manual",
    source_ref: null,
    status: "active",
    summary: "Control de funcion renal.",
    created_by: "playwright.dev",
    results: [
      {
        id: labResultId,
        panel_id: labPanelId,
        patient_id: patientId,
        code: "creatinina",
        name: "Creatinina",
        value: "1.10",
        numeric_value: "1.10",
        unit: "mg/dL",
        reference_range: "0.7-1.3",
        flag: "normal",
        status: "active",
        notes: null,
        created_at: createdAt,
        updated_at: createdAt,
      },
    ],
    created_at: createdAt,
    updated_at: createdAt,
  },
];
