import { expect, test } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";
const demoEntryId = "51111111-1111-4111-8111-111111111111";

test.describe("print routes", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "desktop-only print smoke");
  });

  test("renders patient paper sheets with development footer", async ({ page }) => {
    await page.goto(`/print/pacientes/${demoPatientId}/ficha`);
    await expect(page.getByRole("heading", { name: "Ficha clinica" })).toBeVisible();
    await expect(page.getByText("Paciente Demo Alfa - DEMO-001")).toBeVisible();
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
    await expect(page.getByRole("heading", { name: "Receta" })).toBeVisible();
    await expect(page.getByText("Prescripcion no habilitada")).toBeVisible();
    await expect(page.getByText("Requiere autenticacion, permisos, firma profesional")).toBeVisible();
  });
});
