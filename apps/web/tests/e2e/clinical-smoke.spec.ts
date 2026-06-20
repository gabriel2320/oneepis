import { expect, test } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";

test("patient ficha renders clinical shell and AI draft area", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/ficha`);

  await expect(page.getByRole("heading", { name: /Paciente Demo Alfa/ })).toBeVisible();
  await expect(page.getByText("Sugerencias Ollama")).toBeVisible();
  await expect(page.getByText(/Borrador IA/)).toBeVisible();
});

test("patient status screen renders governed edit form", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/estado`);

  await expect(page.getByRole("heading", { name: "Estado clinico" })).toBeVisible();
  await expect(page.getByText("Estado y contexto")).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar estado" })).toBeDisabled();
});

test("patient encounters render list and creation screen", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/encuentros`);

  await expect(page.getByText("Encuentro demo")).toBeVisible();
  await expect(page.getByRole("link", { name: "Nuevo" })).toBeVisible();

  await page.goto(`/pacientes/${demoPatientId}/encuentros/nuevo`);
  await expect(page.getByRole("heading", { name: "Nuevo encuentro" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar encuentro" })).toBeDisabled();
});

test("hospitalization beds render active board", async ({ page }) => {
  await page.goto("/hospitalizacion/camas");

  await expect(page.getByRole("heading", { name: "Camas" })).toBeVisible();
  await expect(page.getByText("Hospitalizacion demo")).toBeVisible();
  await expect(page.getByText("Medicina / 301 / Cama A")).toBeVisible();
});

test("SOAP editor exposes Ollama review without autosave", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/evoluciones/nueva`);

  await expect(page.getByRole("heading", { name: "Nueva evolucion SOAP" })).toBeVisible();
  const encounterSelect = page.locator('select[name="encounter_id"]');
  await expect(encounterSelect).toContainText("Encuentro demo - ambulatory");
  await expect(page.getByRole("button", { name: "Revisar con Ollama" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar borrador" })).toBeVisible();
});

test("AI settings and print routes render", async ({ page }) => {
  await page.goto("/configuracion/ia");
  await expect(page.getByRole("heading", { name: "IA local" })).toBeVisible();
  await expect(page.getByText("Estado Ollama")).toBeVisible();

  await page.goto(`/print/pacientes/${demoPatientId}/ficha`);
  await expect(page.getByRole("heading", { name: "Ficha clinica" })).toBeVisible();
  await expect(page.getByText("Documento de desarrollo / no uso clinico real.")).toBeVisible();
});

test("login route renders local auth form", async ({ page }) => {
  await page.goto("/login");

  await expect(page.getByRole("heading", { name: "Ingresar" })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Clave")).toBeVisible();
});
