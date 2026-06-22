import { expect, test } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";
const demoHospitalizedPatientId = "12222222-2222-4222-8222-222222222222";

test("patients index renders clinical work queue", async ({ page }) => {
  await page.goto("/pacientes");

  await expect(page.getByRole("heading", { name: "Pacientes" })).toBeVisible();
  await expect(page.getByText("Mesa clinica")).toBeVisible();
  await expect(page.getByText("Fichas visibles", { exact: true })).toBeVisible();
  await expect(page.getByText("Hospitalizadas", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Mesa de pacientes")).toBeVisible();
  await expect(page.getByText("Paciente Demo Alfa")).toBeVisible();
});

test("patient ficha renders clinical shell and AI draft area", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/ficha`);

  await expect(page.getByRole("heading", { name: /Paciente Demo Alfa/ })).toBeVisible();
  await expect(page.getByText("Sugerencias Ollama")).toBeVisible();
  await expect(page.getByText(/Borrador IA/)).toBeVisible();
});

test("AI-Chart renders event proposals from written entries", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/ai-chart`);

  await expect(page.getByRole("heading", { name: "AI-Chart Core" })).toBeVisible();
  await expect(page.getByText("Eventos desde evolucion")).toBeVisible();
  await expect(page.getByText("Estado operativo")).toBeVisible();
  await expect(page.getByText("Seleccionados")).toBeVisible();
  await expect(page.getByText("propuesta revisable")).toBeVisible();
  await expect(
    page.getByText("Estados: pendiente / registrando / registrada en ficha / rechazada."),
  ).toBeVisible();
  await expect(page.getByText("Modo demo: no se generan borradores reales.")).toBeVisible();
  await expect(page.getByText("Modo demo: no se ejecutan intenciones reales.").first()).toBeVisible();
  await expect(page.getByText("Modo demo: no se generan propuestas reales.")).toBeVisible();
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

  await expect(page.getByRole("heading", { name: "Camas", exact: true })).toBeVisible();
  await expect(page.getByText("Hospitalizacion demo")).toBeVisible();
  await expect(page.getByText("Ingreso sin cama demo").first()).toBeVisible();
  await expect(page.getByText("Medicina / 301 / Cama A").first()).toBeVisible();
  await expect(page.getByText("Medicina / 302 / Cama B")).toBeVisible();
  await expect(page.getByText("Administracion de camas")).toBeVisible();
  await expect(page.getByText("Ocupada")).toBeVisible();
  await expect(page.getByLabel("Asignar ingreso a Medicina / 302 / Cama B")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Asignar" })).toBeDisabled();

  await page.getByRole("link", { name: "Nueva cama" }).click();
  await expect(page.getByRole("heading", { name: "Nueva cama" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar cama" })).toBeDisabled();
});

test("hospital rounds render active read-only worklist", async ({ page }) => {
  await page.goto("/hospitalizacion/rondas");

  await expect(page.getByRole("heading", { name: "Rondas" })).toBeVisible();
  await expect(page.getByText("Ronda activa")).toBeVisible();
  await expect(page.getByText("Paciente Demo Beta")).toBeVisible();
  await expect(page.getByText("Medicina / 301 / Cama A")).toBeVisible();
  await expect(page.getByText("Ultima hoja diaria 2026-06-20")).toBeVisible();
  await expect(page.getByText("Hoja diaria demo para validar flujo hospitalizado")).toBeVisible();
  await expect(page.getByText("Ingreso sin cama demo")).toBeVisible();
  await expect(page.getByText("Sin hoja diaria para este ingreso")).toBeVisible();
});

test("hospital daily sheet renders patient workspace", async ({ page }) => {
  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/hoja-diaria`);

  await expect(page.getByRole("heading", { name: "Hoja diaria hospitalizada" })).toBeVisible();
  const dailySheetCard = page.getByRole("article").filter({ hasText: "Hoja diaria 2026-06-20" });
  await expect(dailySheetCard).toBeVisible();
  await expect(dailySheetCard.getByText("Borrador")).toBeVisible();
  await expect(page.getByText("Hoja diaria demo para validar flujo hospitalizado")).toBeVisible();
  await expect(page.getByRole("link", { name: "Editar" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar hoja diaria" })).toBeDisabled();

  await page.getByRole("link", { name: "Editar" }).click();
  await expect(page.getByRole("heading", { name: "Editar hoja diaria" })).toBeVisible();
  await expect(page.locator("textarea").first()).toHaveValue(
    "Hoja diaria demo para validar flujo hospitalizado sin datos reales.",
  );
  await expect(page.getByRole("button", { name: "Guardar cambios" })).toBeDisabled();
});

test("hospital indications render governed draft workspace", async ({ page }) => {
  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/indicaciones`);

  await expect(page.getByRole("heading", { name: "Indicaciones hospitalarias" })).toBeVisible();
  await expect(page.getByText("Borradores registrados")).toBeVisible();
  await expect(page.getByText("Borrador de indicacion demo")).toBeVisible();
  await expect(page.getByText("Borrador hospitalario; no sustituye firma")).toBeVisible();
  await expect(page.getByRole("link", { name: "Imprimir", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cerrar borrador" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Guardar borrador" })).toBeDisabled();
});

test("ambulatory visit renders linked encounter workspace", async ({ page }) => {
  await page.goto(`/consulta/pacientes/${demoPatientId}/atencion`);

  await expect(page.getByRole("heading", { name: "Atencion ambulatoria" })).toBeVisible();
  await expect(page.getByText("Encuentro ambulatorio y evolucion SOAP vinculada.")).toBeVisible();
  await expect(page.getByText("Encuentro demo")).toBeVisible();
  await expect(page.getByText("Control clinico demo")).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar atencion" })).toBeDisabled();
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
