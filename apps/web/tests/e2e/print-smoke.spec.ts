import { expect, test } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";
const demoEntryId = "51111111-1111-4111-8111-111111111111";
const demoHospitalizedPatientId = "12222222-2222-4222-8222-222222222222";
const demoDailySheetId = "a2222222-2222-4222-8222-222222222222";
const demoHospitalIndicationId = "b2222222-2222-4222-8222-222222222222";
const PRINT_NO_PRODUCTION_FOOTER = "Documento de desarrollo / no PHI / no uso clinico real.";

test.describe("print routes", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name !== "chromium", "desktop-only print smoke");
  });

  test("@smoke @print renders patient paper sheets with development footer", async ({ page }) => {
    await page.goto(`/print/pacientes/${demoPatientId}/ficha`);
    await expect(page.getByRole("heading", { name: "Ficha clinica" })).toBeVisible();
    await expect(page.getByText("Paciente Demo Alfa - DEMO-001")).toBeVisible();
    await expect(page.getByText("Vista papel")).toBeVisible();
    await expect(page.getByText("Hoja carta con footer de desarrollo.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Imprimir" })).toBeVisible();
    await expect(page.getByText("Desarrollo", { exact: true })).toBeVisible();
    await expect(page.getByText("Estado ficha:")).toBeVisible();
    await expect(page.getByText("Metadata documental")).toBeVisible();
    await expect(page.getByText("Fuente: record paciente")).toBeVisible();
    await expect(page.getByText("Estado: Ficha de lectura no firmada")).toBeVisible();
    await expect(page.getByText("Diagnosticos historicos")).toBeVisible();
    await expect(page.getByText("Diagnostico historico demo")).toBeVisible();
    await expect(page.getByText("Fuente: Evento curado demo / Codigo: DX-H001")).toBeVisible();
    await expect(page.getByText("Lectura historica demo; no es problema activo.")).toBeVisible();
    await expect(page.getByText(PRINT_NO_PRODUCTION_FOOTER)).toBeVisible();

    await page.goto(`/print/pacientes/${demoPatientId}/resumen`);
    await expect(page.getByRole("heading", { name: "Resumen", exact: true })).toBeVisible();
    await expect(page.getByText("Resumen IA")).toBeVisible();
    await expect(page.getByText("Estado: Resumen no persistido")).toBeVisible();
    await expect(page.getByText("No se imprime contenido IA persistido.")).toBeVisible();

    await page.goto(`/print/pacientes/${demoPatientId}/evolucion/${demoEntryId}`);
    await expect(page.getByRole("heading", { name: "Evolucion SOAP" })).toBeVisible();
    await expect(page.getByText(`Fuente: clinical entry ${demoEntryId}`)).toBeVisible();
    await expect(page.getByText("Estado: signed")).toBeVisible();
    await expect(page.getByText("Control clinico demo")).toBeVisible();
    await expect(page.getByText("Mantener seguimiento y registrar cambios relevantes.")).toBeVisible();

    await page.goto(`/print/pacientes/${demoPatientId}/receta`);
    await expect(page.getByRole("heading", { name: "Receta bloqueada" })).toBeVisible();
    await expect(page.getByText("No emitir como receta clinica")).toBeVisible();
    await expect(page.getByText("Documento bloqueado: no valido para prescribir")).toBeVisible();
    await expect(page.getByText("Requisitos no cumplidos")).toBeVisible();
    await expect(page.getByText("Falta firma profesional habilitada.")).toBeVisible();
    await expect(page.getByText("Falta folio institucional verificable.")).toBeVisible();
    await expect(page.getByText("Falta actor prescriptor con permisos de receta.")).toBeVisible();
    await expect(page.getByText("Falta fecha clinica de emision.")).toBeVisible();
    await expect(page.getByText("Falta politica de prescripcion activa.")).toBeVisible();
    await expect(page.getByText("Firma profesional habilitada.", { exact: true })).toHaveCount(0);
    await expect(page.getByText("Folio institucional verificable.", { exact: true })).toHaveCount(0);

    await page.goto(
      `/print/hospitalizacion/pacientes/${demoHospitalizedPatientId}/hoja-diaria/${demoDailySheetId}`,
    );
    await expect(page.getByRole("heading", { name: "Evolucion diaria hospitalaria" })).toBeVisible();
    await expect(page.getByText(`Fuente: evolucion diaria ${demoDailySheetId}`)).toBeVisible();
    await expect(page.getByText("Hoja diaria demo para validar flujo hospitalizado")).toBeVisible();
    await expect(page.getByText(PRINT_NO_PRODUCTION_FOOTER)).toBeVisible();

    await page.goto(
      `/print/hospitalizacion/pacientes/${demoHospitalizedPatientId}/indicacion/${demoHospitalIndicationId}`,
    );
    await expect(page.getByRole("heading", { name: "Indicacion hospitalaria" })).toBeVisible();
    await expect(page.getByText(`Fuente: indicacion hospitalaria ${demoHospitalIndicationId}`)).toBeVisible();
    await expect(page.getByText("Borrador no firmado")).toBeVisible();
    await expect(page.getByText("Borrador de indicacion demo")).toBeVisible();
    await expect(page.getByText(PRINT_NO_PRODUCTION_FOOTER)).toBeVisible();

    await page.goto(
      `/print/hospitalizacion/pacientes/${demoHospitalizedPatientId}/indicacion/00000000-0000-4000-8000-000000000000`,
    );
    await expect(page.getByText("Indicacion no encontrada.")).toBeVisible();
    await expect(page.getByText("Borrador de indicacion demo")).not.toBeVisible();

    await page.goto("/print/hospitalizacion/rondas");
    await expect(page.getByRole("heading", { name: "Evolucion diaria hospitalaria" })).toBeVisible();
    await expect(page.getByText("Paciente Demo Beta")).toBeVisible();
    await expect(page.getByText("Medicina / 301 / Cama A")).toBeVisible();
    await expect(page.getByText("Ultima evolucion diaria 2026-06-20 - Borrador")).toBeVisible();
    await expect(page.getByText("Sin evolucion diaria para este ingreso")).toBeVisible();
    await expect(page.getByText(PRINT_NO_PRODUCTION_FOOTER)).toBeVisible();
  });
});
