import { expect, test } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";

test("patient ficha renders clinical shell and AI draft area", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/ficha`);

  await expect(page.getByRole("heading", { name: /Paciente Demo Alfa/ })).toBeVisible();
  await expect(page.getByText("Sugerencias Ollama")).toBeVisible();
  await expect(page.getByText(/Borrador IA/)).toBeVisible();
});

test("SOAP editor exposes Ollama review without autosave", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/evoluciones/nueva`);

  await expect(page.getByRole("heading", { name: "Nueva evolucion SOAP" })).toBeVisible();
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
