import { expect, test } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";
const demoEntryId = "51111111-1111-4111-8111-111111111111";
const demoHospitalizedPatientId = "12222222-2222-4222-8222-222222222222";
const demoDailySheetId = "a2222222-2222-4222-8222-222222222222";
const demoHospitalIndicationId = "b2222222-2222-4222-8222-222222222222";

test.describe("print routes", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "desktop-only print smoke");
  });

  test("renders patient paper sheets with development footer", async ({ page }) => {
    await page.goto(`/print/pacientes/${demoPatientId}/ficha`);
    await expect(page.getByRole("heading", { name: "Ficha clinica" })).toBeVisible();
    await expect(page.getByText("Paciente Demo Alfa - DEMO-001")).toBeVisible();
    await expect(page.getByText("Vista papel")).toBeVisible();
    await expect(page.getByText("Hoja carta con footer de desarrollo.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Imprimir" })).toBeVisible();
    await expect(page.getByText("Documento de desarrollo / no uso clinico real.")).toBeVisible();

    await page.goto(`/print/pacientes/${demoPatientId}/resumen`);
    await expect(page.getByRole("heading", { name: "Resumen", exact: true })).toBeVisible();
    await expect(page.getByText("Resumen IA")).toBeVisible();
    await expect(page.getByText("No se imprime contenido IA persistido.")).toBeVisible();

    await page.goto(`/print/pacientes/${demoPatientId}/evolucion/${demoEntryId}`);
    await expect(page.getByRole("heading", { name: "Evolucion SOAP" })).toBeVisible();
    await expect(page.getByText("Control clinico demo")).toBeVisible();
    await expect(page.getByText("Mantener seguimiento y registrar cambios relevantes.")).toBeVisible();

    await page.goto(`/print/pacientes/${demoPatientId}/receta`);
    await expect(page.getByRole("heading", { name: "Receta bloqueada" })).toBeVisible();
    await expect(page.getByText("No emitir como receta clinica")).toBeVisible();
    await expect(page.getByText("Documento bloqueado: no valido para prescribir")).toBeVisible();

    await page.goto(
      `/print/hospitalizacion/pacientes/${demoHospitalizedPatientId}/hoja-diaria/${demoDailySheetId}`,
    );
    await expect(page.getByRole("heading", { name: "Hoja diaria hospitalizada" })).toBeVisible();
    await expect(page.getByText("Hoja diaria demo para validar flujo hospitalizado")).toBeVisible();
    await expect(page.getByText("Documento de desarrollo / no uso clinico real.")).toBeVisible();

    await page.goto(
      `/print/hospitalizacion/pacientes/${demoHospitalizedPatientId}/indicacion/${demoHospitalIndicationId}`,
    );
    await expect(page.getByRole("heading", { name: "Indicacion hospitalaria" })).toBeVisible();
    await expect(page.getByText("Borrador no firmado")).toBeVisible();
    await expect(page.getByText("Borrador de indicacion demo")).toBeVisible();
    await expect(page.getByText("Documento de desarrollo / no uso clinico real.")).toBeVisible();

    await page.goto(
      `/print/hospitalizacion/pacientes/${demoHospitalizedPatientId}/indicacion/00000000-0000-4000-8000-000000000000`,
    );
    await expect(page.getByText("Indicacion no encontrada.")).toBeVisible();
    await expect(page.getByText("Borrador de indicacion demo")).not.toBeVisible();

    await page.goto("/print/hospitalizacion/rondas");
    await expect(page.getByRole("heading", { name: "Ronda hospitalaria" })).toBeVisible();
    await expect(page.getByText("Paciente Demo Beta")).toBeVisible();
    await expect(page.getByText("Medicina / 301 / Cama A")).toBeVisible();
    await expect(page.getByText("Ultima hoja diaria 2026-06-20 - Borrador")).toBeVisible();
    await expect(page.getByText("Sin hoja diaria para este ingreso")).toBeVisible();
    await expect(page.getByText("Documento de desarrollo / no uso clinico real.")).toBeVisible();
  });
});
