import { expect, test, type Page, type Route } from "@playwright/test";

const patientId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const catalogItemId = "10000000-0000-4000-8000-000000000101";

test.skip(
  process.env.NEXT_PUBLIC_DEMO_MODE !== "false",
  "Medication vademecum real UI runs in the dedicated non-demo e2e command.",
);

test("Medication page renders vademecum and dose validation without executable prescription", async ({
  page,
}) => {
  await mockClinicalApi(page);

  await page.goto(`/pacientes/${patientId}/medicacion`);

  await expect(page.getByText("Vademecum", { exact: true })).toBeVisible();
  await expect(page.getByText("Analgesico demo 500 mg comprimido").first()).toBeVisible();
  await page.getByLabel("Agregar favorito").first().click();
  await expect(page.getByText("Favoritos", { exact: true })).toBeVisible();
  await expect(page.getByText("Dosis y alertas")).toBeVisible();
  await expect(page.getByText("no consulta FDA/openFDA en vivo")).toBeVisible();

  await page.goto(
    `/pacientes/${patientId}/medicacion/nueva?catalogItemId=${catalogItemId}` +
      "&name=Analgesico%20demo%20500%20mg%20comprimido&route=oral",
  );
  await page.locator("input").nth(1).fill("1500 mg");
  await page.getByRole("button", { name: "Validar dosis" }).click();

  await expect(page.getByText("Alerta de dosis")).toBeVisible();
  await expect(page.getByText("Dosis 1500 fuera del rango curado")).toBeVisible();
  await expect(page.getByText("Justificacion de override")).toBeVisible();
  await expect(page.getByText("No crea receta valida")).toBeVisible();
});

async function mockClinicalApi(page: Page) {
  await page.route("http://127.0.0.1:8000/api/v1/**", async (route) => {
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
  if (path === `/api/v1/patients/${patientId}/record`) {
    await route.fulfill({ json: patientRecord, headers: corsHeaders });
    return;
  }
  if (path === "/api/v1/medication-catalog") {
    await route.fulfill({ json: [catalogItem], headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/medication-drafting-context`) {
    await route.fulfill({ json: draftingContext, headers: corsHeaders });
    return;
  }
  if (path === `/api/v1/patients/${patientId}/medications/validate-draft`) {
    await route.fulfill({ json: validationResponse, headers: corsHeaders });
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
  last_name: "Medicacion",
  birth_date: "1980-01-01",
  sex_at_birth: "unknown",
  clinical_status: "active",
  current_care_context: "ambulatory",
  clinical_identifier: "MED-001",
  created_at: createdAt,
  updated_at: createdAt,
};

const medication = {
  id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  patient_id: patientId,
  catalog_item_id: catalogItemId,
  name: "Analgesico demo 500 mg comprimido",
  dose: "500 mg",
  route: "oral",
  frequency: "cada 8 horas",
  status: "active",
  started_on: "2026-06-20",
  ended_on: null,
  dose_check_snapshot: {},
  dose_override_reason: null,
  created_at: createdAt,
  updated_at: createdAt,
};

const patientRecord = {
  patient,
  latest_vitals: null,
  active_allergies: [],
  active_medications: [medication],
  active_problems: [],
  recent_entries: [],
};

const catalogItem = {
  id: catalogItemId,
  source_system: "local_curated",
  source_label: "Fixture demo OneEpis; no uso clinico",
  source_url: null,
  external_id: null,
  source_version: null,
  retrieved_at: null,
  reviewed_at: null,
  review_status: "reviewed",
  display_name: "Analgesico demo 500 mg comprimido",
  generic_name: "analgesico-demo",
  form: "comprimido",
  strength: "500 mg",
  route: "oral",
  status: "available",
  tags: ["demo"],
  dose_rules: [
    {
      id: "10000000-0000-4000-8000-000000000201",
      catalog_item_id: catalogItemId,
      source_system: "local_curated",
      source_label: "Fixture demo OneEpis; no uso clinico",
      source_url: null,
      external_id: null,
      source_version: null,
      retrieved_at: null,
      reviewed_at: null,
      review_status: "reviewed",
      population: "adult_general_demo",
      route: "oral",
      unit: "mg",
      min_value: "100",
      max_value: "1000",
      frequency_text: "cada 6-8 horas",
      usual_dose_text: "Rango demo: 100-1000 mg por dosis.",
      avoid_dose_text: "Evitar dosis demo sobre 1000 mg por toma sin justificacion.",
      severity: "warning",
      created_at: createdAt,
      updated_at: createdAt,
    },
  ],
  created_at: createdAt,
  updated_at: createdAt,
};

const draftingContext = {
  active_medications: [medication],
  recent_medications: [medication],
  previous_day_indication_texts: [],
  suggested_catalog_items: [catalogItem],
  limitations: ["Contexto de borrador: no crea receta valida, orden ejecutable, firma ni folio."],
  applies_changes: false,
};

const validationResponse = {
  warnings: [
    {
      severity: "warning",
      message: "Dosis 1500 fuera del rango curado (100-1000 mg)",
      requires_override: true,
      rule_id: "10000000-0000-4000-8000-000000000201",
      source: {
        source_system: "local_curated",
        source_label: "Fixture demo OneEpis; no uso clinico",
        source_url: null,
        external_id: null,
        source_version: null,
        retrieved_at: null,
        reviewed_at: null,
        review_status: "reviewed",
      },
    },
  ],
  blocking: true,
  limitations: ["Pediatria, embarazo, renal/hepatica e interacciones requieren regla explicita."],
  source_refs: [],
  normalized_dose: { value: "1500", raw: "1500 mg" },
  applies_changes: false,
};
