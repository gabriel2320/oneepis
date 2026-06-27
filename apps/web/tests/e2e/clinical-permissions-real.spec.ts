import { expect, test } from "@playwright/test";

import {
  ambulatoryPermissionsPatientId,
  mockAmbulatoryVisitApi,
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

test("solo_lectura reads ambulatory visit but cannot write", async ({ page }) => {
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

test("enfermeria can open preconsult but cannot save ambulatory visit", async ({ page }) => {
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
