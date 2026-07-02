import { expect, test } from "@playwright/test";

import {
  ambulatoryPermissionsPatientId,
  mockAmbulatoryVisitApi,
  mockPatientIndexApi,
  type MockAuthUser,
} from "./helpers/clinical-api-mock";

const visitPath = `/consulta/pacientes/${ambulatoryPermissionsPatientId}/atencion`;

const readOnlyUser: MockAuthUser = {
  email: "lector@oneepis.local",
  name: "Lectura E2E",
  roles: ["solo_lectura"],
  actor_id: "e2e-lector",
};

const nursingUser: MockAuthUser = {
  email: "enfermeria@oneepis.local",
  name: "Enfermeria E2E",
  roles: ["enfermeria"],
  actor_id: "e2e-enfermeria",
};

test.skip(
  process.env.NEXT_PUBLIC_DEMO_MODE !== "false",
  "Clinical permissions real UI runs in the dedicated non-demo e2e command.",
);

test("@auth @patient solo_lectura sees authorized empty patient index", async ({ page }) => {
  await mockPatientIndexApi(page, { authUser: readOnlyUser, patients: [] });

  await page.goto("/pacientes");

  await expect(page.getByRole("heading", { name: "Pacientes" })).toBeVisible();
  await expect(page.getByText("0 fichas visibles")).toBeVisible();
  await expect(page.getByText("Sin fichas visibles")).toBeVisible();
  await expect(
    page.getByText("No hay fichas visibles para tu relacion asistencial activa."),
  ).toBeVisible();
  const deniedActions = page.getByRole("button", { name: "Sin permiso" });
  await expect(deniedActions).toHaveCount(2);
  await expect(deniedActions.first()).toBeDisabled();
  await expect(deniedActions.nth(1)).toBeDisabled();
  await expect(page.getByText("Crea la primera ficha de desarrollo")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Crear paciente" })).toHaveCount(0);
});

test("@auth @patient solo_lectura reads ambulatory visit but cannot write", async ({ page }) => {
  await mockAmbulatoryVisitApi(page, { authUser: readOnlyUser });

  await page.goto(visitPath);

  await expect(page.getByRole("heading", { name: "Atencion ambulatoria" })).toBeVisible();
  await expect(page.getByText("Nota clinica libre", { exact: true }).first()).toBeVisible();
  await expect(
    page.getByText("Tu perfil no tiene permiso para crear atencion ambulatoria."),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar atencion" })).toBeDisabled();

  await page.locator("details").filter({ hasText: "Preconsulta ambulatoria" }).locator("summary").click();
  await expect(
    page.getByText("Tu perfil no tiene permiso para registrar preconsulta completa."),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Registrar preconsulta" })).toBeDisabled();
});

test("@auth @patient enfermeria can open preconsult but cannot save ambulatory visit", async ({ page }) => {
  await mockAmbulatoryVisitApi(page, { authUser: nursingUser });

  await page.goto(visitPath);

  await expect(page.getByRole("heading", { name: "Atencion ambulatoria" })).toBeVisible();
  await expect(
    page.getByText("Tu perfil no tiene permiso para crear atencion ambulatoria."),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar atencion" })).toBeDisabled();

  await page.locator("details").filter({ hasText: "Preconsulta ambulatoria" }).locator("summary").click();
  await expect(page.getByLabel("Cita para preconsulta")).toContainText("Control ambulatorio permisos");
  await expect(
    page.getByText("Tu perfil no tiene permiso para registrar preconsulta completa."),
  ).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Registrar preconsulta" })).toBeEnabled();
});
