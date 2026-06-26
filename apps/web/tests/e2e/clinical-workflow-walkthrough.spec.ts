import { expect, test, type Locator, type Page } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";
const demoHospitalizedPatientId = "12222222-2222-4222-8222-222222222222";

test("canonical clinical walkthrough stays oriented by workplace and reconciles in patient record", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "chromium", "desktop walkthrough uses side navigation");

  await page.goto("/login");
  await expectCleanLogin(page);

  await page.goto("/");
  await expect(page).toHaveURL(/\/home$/);
  await expectHospitalMapOnly(page);

  await openHospitalPlace(page, "Consultas ambulatorias");
  await expect(page).toHaveURL(/\/consulta$/);
  await expectAmbulatoryEntry(page);

  await page.getByRole("link", { name: "Agenda" }).first().click();
  await expect(page).toHaveURL(/\/consulta\/agenda$/);
  await expect(page.getByRole("heading", { name: "Agenda", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Abrir atencion" }).first().click();
  await expect(page).toHaveURL(new RegExp(`/consulta/pacientes/${demoPatientId}/atencion$`));
  await expectAmbulatoryWorkspace(page);

  await page.getByRole("link", { name: "Ficha longitudinal" }).click();
  await expect(page).toHaveURL(new RegExp(`/pacientes/${demoPatientId}/ficha$`));
  await expectPatientRecord(page, "patient");

  await page.getByRole("link", { name: /OneEpis Mapa del hospital/ }).click();
  await expect(page).toHaveURL(/\/home$/);
  await openHospitalPlace(page, "Hospitalizacion");
  await expect(page).toHaveURL(/\/hospitalizacion$/);
  await expectHospitalEntry(page);

  await page.getByRole("link", { name: "Evolucion diaria" }).first().click();
  await expect(page).toHaveURL(/\/hospitalizacion\/rondas$/);
  await page.getByRole("link", { name: "Ingreso" }).first().click();
  await expect(page).toHaveURL(new RegExp(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/ingreso$`));
  await expectHospitalWorkspace(page);

  await page.getByRole("link", { name: "Ficha longitudinal" }).click();
  await expect(page).toHaveURL(new RegExp(`/pacientes/${demoHospitalizedPatientId}/ficha$`));
  await expectPatientRecord(page, "patient");
});

async function expectCleanLogin(page: Page) {
  await expect(page.getByRole("heading", { name: "Ingresar" })).toBeVisible();
  await expect(page.getByLabel("Usuario o correo")).toHaveValue("");
  await expect(page.getByLabel("Contraseña")).toHaveValue("");
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeDisabled();
  await expect(page.getByRole("link", { name: /Pacientes|Consulta|Hospitalizacion/ })).toHaveCount(0);
  await expect(page.getByText("medico@oneepis.local")).toHaveCount(0);
  await expect(page.getByText("Seleccionar rol")).toHaveCount(0);
}

async function expectHospitalMapOnly(page: Page) {
  const main = page.getByRole("main");
  await expect(page.getByRole("heading", { name: "Mapa del hospital" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Consultas ambulatorias" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Hospitalizacion" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Farmacia" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Laboratorio" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Unidad de cuidados intensivos" })).toBeVisible();
  await expect(main.getByRole("button", { name: "Futuro" }).first()).toBeDisabled();
  await expect(main.getByRole("button", { name: "Bloqueado" })).toBeDisabled();
  await expectNoClinicalPayload(main);
  await expectNoActionCards(main);
}

async function openHospitalPlace(page: Page, title: string) {
  const card = page.getByRole("article").filter({ hasText: title });
  await expect(card).toBeVisible();
  await card.getByRole("link", { name: /Entrar|Seleccionar paciente/ }).click();
}

async function expectAmbulatoryEntry(page: Page) {
  const main = page.getByRole("main");
  await expect(page.getByRole("heading", { name: "Consultas ambulatorias" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Navegacion ambulatorio" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Agenda ambulatoria" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Atencion clinica" })).toBeVisible();
  await expect(main.getByText("Hospitalizacion demo")).toHaveCount(0);
  await expect(main.getByText("Indicaciones hospitalarias")).toHaveCount(0);
  await expectNoInternalTerms(main);
}

async function expectAmbulatoryWorkspace(page: Page) {
  const main = page.getByRole("main");
  await expectSemanticShell(page, "ambulatory");
  await expect(page.getByRole("navigation", { name: "Navegacion ambulatoria" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Atencion ambulatoria" })).toBeVisible();
  await expect(main.getByText("Canon ambulatorio")).toBeVisible();
  await expect(main.getByText("Preconsulta ambulatoria")).toBeVisible();
  await expect(main.getByText("No emite diagnostico, receta, orden ni firma.")).toBeVisible();
  await expect(main.getByText("Ingreso medico hospitalario")).toHaveCount(0);
  await expect(main.getByText("Indicaciones hospitalarias")).toHaveCount(0);
  await expectNoInternalTerms(main);
}

async function expectHospitalEntry(page: Page) {
  const main = page.getByRole("main");
  await expect(page.getByRole("heading", { name: "Hospitalizacion" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Navegacion hospitalizacion" })).toBeVisible();
  await expect(main.getByText("Paciente Demo Beta")).toBeVisible();
  await expect(main.getByText("Medicina / 301 / Cama A")).toBeVisible();
  await expect(main.getByText("Atencion ambulatoria")).toHaveCount(0);
  await expect(main.getByText("Preconsulta ambulatoria")).toHaveCount(0);
  await expectNoInternalTerms(main);
}

async function expectHospitalWorkspace(page: Page) {
  const main = page.getByRole("main");
  await expectSemanticShell(page, "hospital");
  await expect(page.getByRole("navigation", { name: "Navegacion hospitalaria" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ingreso medico hospitalario" })).toBeVisible();
  await expect(main.getByText("Borrador de ingreso")).toBeVisible();
  await expect(main.getByText("Atencion ambulatoria")).toHaveCount(0);
  await expect(main.getByText("Preconsulta ambulatoria")).toHaveCount(0);
  await expectNoInternalTerms(main);
}

async function expectPatientRecord(page: Page, workspace: "patient") {
  const main = page.getByRole("main");
  await expectSemanticShell(page, workspace);
  await expect(main.getByText("Hoja clinica viva")).toBeVisible();
  await expect(main.getByText("Mapa longitudinal del paciente")).toBeVisible();
  await expect(main.getByText("El paciente es unico; los episodios separan el contexto")).toBeVisible();
  await expect(main.getByText("Linea clinica longitudinal")).toBeVisible();
  await expect(main.getByText("Antecedentes clinicos")).toBeVisible();
  await expect(main.getByText("Fuentes usadas")).toBeVisible();
  await expectNoInternalTerms(main);
}

async function expectSemanticShell(page: Page, workspace: "patient" | "ambulatory" | "hospital") {
  const shell = page.locator(`[data-workspace="${workspace}"]`);
  await expect(shell).toBeVisible();
  await expect(shell).toHaveAttribute("data-ai-provider-visible", "false");
  await expect(shell).toHaveAttribute("data-internal-roles-hidden", "true");
}

async function expectNoActionCards(locator: Locator) {
  await expect(locator.getByRole("heading", { name: "Nueva evolucion" })).toHaveCount(0);
  await expect(locator.getByRole("heading", { name: "Nueva medicacion" })).toHaveCount(0);
  await expect(locator.getByRole("heading", { name: "Nueva alergia" })).toHaveCount(0);
  await expect(locator.getByRole("heading", { name: "Nuevo problema" })).toHaveCount(0);
  await expect(locator.getByRole("heading", { name: "Nueva cama" })).toHaveCount(0);
  await expect(locator.getByRole("heading", { name: "Receta valida" })).toHaveCount(0);
  await expect(locator.getByRole("heading", { name: "AI-Chart" })).toHaveCount(0);
  await expect(locator.getByRole("heading", { name: "Dashboard" })).toHaveCount(0);
}

async function expectNoClinicalPayload(locator: Locator) {
  await expect(locator.getByText("Paciente Demo Alfa")).toHaveCount(0);
  await expect(locator.getByText("Paciente Demo Beta")).toHaveCount(0);
  await expect(locator.getByText("Fichas visibles")).toHaveCount(0);
  await expect(locator.getByText("Mesa de pacientes")).toHaveCount(0);
  await expect(locator.getByText("Actividad reciente")).toHaveCount(0);
  await expect(locator.getByText("Estadisticas")).toHaveCount(0);
}

async function expectNoInternalTerms(locator: Locator) {
  await expect(locator).not.toContainText(
    /\bworkflow_kind\b|ClinicalEncounter|requiere admin, medico|rol admin|medico, admin|Ollama activo|Ollama pendiente/,
  );
}
