import { expect, test, type Locator, type Page } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";
const demoHospitalizedPatientId = "12222222-2222-4222-8222-222222222222";
const demoIntakeEntryId = "61111111-1111-4111-8111-111111111111";
const demoDischargeSummaryEntryId = "62222222-2222-4222-8222-222222222222";

async function expectSemanticShell(page: Page, workspace: "patient" | "ambulatory" | "hospital") {
  const shell = page.locator(`[data-workspace="${workspace}"]`);
  await expect(shell).toBeVisible();
  await expect(shell).toHaveAttribute("data-ai-provider-visible", "false");
  await expect(shell).toHaveAttribute("data-internal-roles-hidden", "true");
}

async function expectNoInternalTerms(locator: Locator) {
  await expect(locator).not.toContainText(/\bworkflow_kind\b|ClinicalEncounter|requiere admin, medico|rol admin|medico, admin|Ollama activo|Ollama pendiente|Si Ollama esta apagado|aunque Ollama no este disponible/);
}

const FORBIDDEN_CLINICAL_COPY =
  /Canon ambulatorio|workflow_kind|ClinicalEncounter|\bOllama\b|\bdashboard\b|acciones disponibles|bandeja operativa|medico\/admin\/dev/i;

const VISIBLE_CLINICAL_ROUTES = [
  "/login",
  "/home",
  "/pacientes",
  `/pacientes/${demoPatientId}/ficha`,
  `/consulta/pacientes/${demoPatientId}/atencion`,
  "/hospitalizacion",
];

test("patients index renders clinical work queue", async ({ page }) => {
  await page.goto("/pacientes");

  await expect(page.getByRole("heading", { name: "Pacientes" })).toBeVisible();
  await expect(page.getByText("Mesa de pacientes")).toBeVisible();
  await expect(page.getByText("Fichas visibles", { exact: true })).toBeVisible();
  await expect(page.getByText("Hospitalizadas", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Mesa de pacientes")).toBeVisible();
  await expect(page.getByText("Paciente Demo Alfa")).toBeVisible();
});

test("patient ficha renders clinical shell and AI draft area", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/ficha`);
  const main = page.getByRole("main");

  await expectSemanticShell(page, "patient");
  await expect(page.getByRole("heading", { name: /Paciente Demo Alfa/ })).toBeVisible();
  await expect(page.getByText("Hoja clinica viva")).toBeVisible();
  await expect(page.getByText("Linea clinica longitudinal")).toBeVisible();
  await expect(page.getByText("Antecedentes clinicos")).toBeVisible();
  await expect(page.getByText("Problema demo activo")).toBeVisible();
  await expect(page.getByText("Fuentes actuales", { exact: true })).toBeVisible();
  await expect(page.getByText("Sin escritura", { exact: true })).toBeVisible();
  await expect(page.getByText("Fuentes usadas")).toBeVisible();
  await expect(page.getByText("Antecedente activo: 1")).toBeVisible();
  await expect(page.getByText("Alergia: 1")).toBeVisible();
  await expect(page.getByText("Medicacion activa: 1")).toBeVisible();
  await expect(page.getByText("Eventos curados: 0")).toBeVisible();
  await expect(page.getByText("Mapa longitudinal del paciente")).toBeVisible();
  await expect(page.getByText("Contexto operativo")).toBeVisible();
  await expect(page.getByText("Actos con episodio")).toBeVisible();
  await expect(page.getByText("Datos longitudinales", { exact: true })).toBeVisible();
  await expect(page.getByText("El paciente es unico; los episodios separan el contexto")).toBeVisible();
  await expect(page.getByText("Faltantes declarados")).toBeVisible();
  await expect(page.getByText("Linea de tiempo avanzada")).toBeVisible();
  await expect(page.getByText("Fuentes visibles")).toBeVisible();
  await expect(page.getByText("No escribe ficha", { exact: true })).toBeVisible();
  await expect(page.getByText("Timeline avanzado disponible con API real")).toBeVisible();
  await expect(page.getByText("Riesgos clinicos")).toBeVisible();
  await expect(page.getByText("sin scores automaticos")).toBeVisible();
  await expect(page.getByText("Fuente API", { exact: true })).toBeVisible();
  await expect(page.getByText("Sin ordenes", { exact: true })).toBeVisible();
  await expect(page.getByText("Limites visibles y faltantes")).toBeVisible();
  await expect(page.getByText("Limite visible: 3 paneles recientes")).toBeVisible();
  await expect(page.getByText("No hay carga masiva")).toBeVisible();
  await expect(page.getByRole("link", { name: "Ver papel", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Apoyo contextual" })).toBeVisible();
  await expect(page.getByText(/Borrador asistido/)).toBeVisible();
  await expect(page.getByText(/Borrador IA/)).toHaveCount(0);
  await expect(page.getByText("Tu rol actual no permite")).toHaveCount(0);
  await expectNoInternalTerms(main);
});

test("patient navigation groups clinical areas on desktop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium", "desktop sidebar only");

  await page.goto(`/pacientes/${demoPatientId}/ficha`);

  await expect(page.getByRole("link", { name: /OneEpis Mapa del hospital/ })).toHaveAttribute(
    "href",
    "/home",
  );
  const nav = page.getByRole("navigation", { name: "Navegacion paciente" });
  await expect(nav.getByText("Ficha", { exact: true })).toBeVisible();
  await expect(nav.getByText("Ambulatorio", { exact: true })).toBeVisible();
  await expect(nav.getByText("Hospitalizado", { exact: true })).not.toBeVisible();
  await expect(nav.getByText("IA", { exact: true })).toBeVisible();
  await expect(nav.getByText("Control", { exact: true })).toBeVisible();
  await expect(nav.getByRole("link", { name: /Atencion clinica/ })).toBeVisible();
  await expect(nav.getByRole("link", { name: /AI-Chart/ })).toBeVisible();
  await expect(nav.getByRole("link", { name: /Auditoria/ })).toBeVisible();

  await page.goto(`/pacientes/${demoHospitalizedPatientId}/ficha`);
  const hospitalNav = page.getByRole("navigation", { name: "Navegacion paciente" });
  await expect(hospitalNav.getByText("Hospitalizado", { exact: true })).toBeVisible();
  await expect(hospitalNav.getByText("Ambulatorio", { exact: true })).not.toBeVisible();
  await expect(hospitalNav.getByRole("link", { name: /Ingreso/ })).toBeVisible();
  await expect(hospitalNav.getByRole("link", { name: /Evolucion diaria/ })).toBeVisible();
});

test("patient navigation mobile selector changes sections", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile selector only");

  await page.goto(`/pacientes/${demoPatientId}/ficha`);

  const selector = page.getByLabel("Seccion clinica");
  await expect(selector).toBeVisible();
  await selector.selectOption("atencion-ambulatoria");
  await expect(page).toHaveURL(new RegExp(`/consulta/pacientes/${demoPatientId}/atencion$`));
  await expect(page.getByRole("heading", { name: "Atencion ambulatoria" })).toBeVisible();
});

test("AI-Chart renders event proposals from written entries", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/ai-chart`);
  const main = page.getByRole("main");

  await expectSemanticShell(page, "patient");
  await expect(page.getByRole("heading", { name: "AI-Chart Core" })).toBeVisible();
  await expect(page.getByText("Leer contexto")).toBeVisible();
  await expect(page.getByText("Seleccionar evidencia")).toBeVisible();
  await expect(page.getByText("Revisar propuestas")).toBeVisible();
  await expect(page.getByText("Eventos desde evolucion")).toBeVisible();
  await expect(page.getByText("Estado operativo")).toBeVisible();
  await expect(page.getByText("Seleccionados")).toBeVisible();
  await expect(page.getByText("propuesta revisable")).toBeVisible();
  await expect(page.getByText("Si la IA local esta apagada, se usa degradacion local.")).toBeVisible();
  await expect(
    page.getByText("AI-Chart mantiene reglas, plantillas y auditoria aunque la IA local no este disponible."),
  ).toBeVisible();
  await expect(page.getByText("IA clinica:")).toBeVisible();
  await expectNoInternalTerms(main);
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

test("patient events expose curation presets for patient core", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/eventos`);

  await expect(page.getByRole("heading", { name: "Eventos clinicos" })).toBeVisible();
  await expect(page.getByText("Curaduria minima para ficha tradicional")).toBeVisible();
  await expect(page.getByRole("button", { name: "Diagnostico historico" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Procedimiento previo" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Antecedente familiar/social" })).toBeDisabled();
  await expect(page.getByText("fuente y limite visible")).toBeVisible();
});

test("patient support data routes stay secondary", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/encuentros`);

  await expect(page.getByText("Encuentro demo").first()).toBeVisible();
  await expect(page.getByText("Atenciones e ingresos vinculados")).toBeVisible();
  await expect(page.getByRole("link", { name: "Registrar soporte" })).toBeVisible();

  await page.goto(`/pacientes/${demoPatientId}/encuentros/nuevo`);
  await expect(page.getByRole("heading", { name: "Registrar atencion o ingreso" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar encuentro" })).toBeDisabled();
});

test("hospitalization home renders compact operational board", async ({ page }) => {
  await page.goto("/hospitalizacion");
  const main = page.getByRole("main");

  await expect(page.getByRole("heading", { name: "Hospitalizacion" })).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Navegacion hospitalizacion" });
  await expect(nav.getByRole("link", { name: "Estacion hospitalaria" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Camas" })).toBeVisible();
  await expect(nav.getByText("Agenda", { exact: true })).toHaveCount(0);
  await expect(nav.getByText("Seleccionar paciente", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Ingresos activos")).toBeVisible();
  await expect(page.getByText("Sin cama", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Ver evolucion completa" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Trabajo hospitalario de hoy" })).toBeVisible();
  await expect(page.getByText("Paciente Demo Beta")).toBeVisible();
  await expect(page.getByText("Medicina / 301 / Cama A")).toBeVisible();
  await expect(page.getByText("Ingreso sin cama demo")).toBeVisible();
  await expect(page.getByRole("link", { name: "Administrar camas" })).toBeVisible();
  await expect(page.getByText("Administracion de camas")).not.toBeVisible();
  await expect(main.getByText("Atencion ambulatoria")).toHaveCount(0);
  await expect(main.getByText("Preconsulta ambulatoria")).toHaveCount(0);
  await expect(main.getByText("Control ambulatorio demo")).toHaveCount(0);
  await expectNoInternalTerms(main);
});

test("hospitalization beds render active board", async ({ page }) => {
  await page.goto("/hospitalizacion/camas");

  await expect(page.getByRole("heading", { name: "Camas", exact: true })).toBeVisible();
  await expect(page.getByText("Hospitalizacion demo")).toBeVisible();
  await expect(page.getByText("Ingreso sin cama demo").first()).toBeVisible();
  await expect(page.getByText("Medicina / 301 / Cama A").first()).toBeVisible();
  await expect(page.getByText("Medicina / 302 / Cama B")).toBeVisible();
  await expect(page.getByText("Administracion de camas")).toBeVisible();
  await expect(page.getByText("Ocupada").first()).toBeVisible();
  await expect(page.getByLabel("Asignar ingreso a Medicina / 302 / Cama B")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Asignar" }).first()).toBeDisabled();

  await page.getByRole("link", { name: "Registrar cama" }).click();
  await expect(page.getByRole("heading", { name: "Registrar cama" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar cama" })).toBeDisabled();
});

test("hospital daily evolution renders active read-only worklist", async ({ page }) => {
  await page.goto("/hospitalizacion/rondas");

  await expect(page.getByRole("heading", { name: "Evolucion diaria hospitalaria" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pacientes hospitalizados" })).toBeVisible();
  await expect(page.getByText("Paciente Demo Beta")).toBeVisible();
  await expect(page.getByText("Medicina / 301 / Cama A")).toBeVisible();
  await expect(page.getByText("Ultima evolucion diaria 2026-06-20")).toBeVisible();
  await expect(page.getByText("Hoja diaria demo para validar flujo hospitalizado")).toBeVisible();
  await expect(page.getByText("Ingreso sin cama demo")).toBeVisible();
  await expect(page.getByText("Sin evolucion diaria para este ingreso")).toBeVisible();
  await expect(page.getByRole("link", { name: /Ingreso/ }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Epicrisis/ }).first()).toBeVisible();
});

test("hospital admission renders governed intake draft workspace", async ({ page }) => {
  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/ingreso`);

  await expectSemanticShell(page, "hospital");
  await expect(page.getByRole("heading", { name: "Ingreso medico hospitalario" })).toBeVisible();
  await expect(page.getByText("Borrador de ingreso")).toBeVisible();
  await expect(page.getByLabel("Hospitalizacion activa")).toContainText("Hospitalizacion demo");
  await expect(page.getByText("Sin ingreso medico registrado")).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar ingreso" })).toBeDisabled();
  await expect(page.getByText("Atencion ambulatoria")).toHaveCount(0);
  await expect(page.getByText("Preconsulta ambulatoria")).toHaveCount(0);
  await expectNoInternalTerms(page.getByRole("main"));
});

test("hospital domain navigation is isolated on desktop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium", "desktop sidebar only");

  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/ingreso`);

  const nav = page.getByRole("navigation", { name: "Navegacion hospitalaria" });
  await expect(nav).toBeVisible();
  await expect(nav.getByRole("link", { name: "Ingreso" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Evolucion diaria" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Indicaciones" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Epicrisis" })).toBeVisible();
  await expect(nav.getByText("Agenda", { exact: true })).toHaveCount(0);
  await expect(nav.getByText("Atencion clinica", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Nueva SOAP" })).toHaveCount(0);
});

test("hospital discharge summary renders governed draft workspace", async ({ page }) => {
  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/epicrisis`);

  await expect(page.getByRole("heading", { name: "Alta y epicrisis" })).toBeVisible();
  await expect(page.getByText("Borrador de epicrisis")).toBeVisible();
  await expect(page.getByLabel("Hospitalizacion para epicrisis")).toContainText("Hospitalizacion demo");
  await expect(page.getByText("Epicrisis preliminar demo")).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar epicrisis" })).toBeDisabled();
  await expect(page.getByText("Atencion ambulatoria")).toHaveCount(0);
  await expect(page.getByText("Preconsulta ambulatoria")).toHaveCount(0);
  await expect(page.getByText("workflow_kind")).toHaveCount(0);
  await expect(page.getByText("ClinicalEncounter")).toHaveCount(0);
});

test("hospital daily sheet renders patient workspace", async ({ page }) => {
  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/hoja-diaria`);

  await expect(page.getByRole("heading", { name: "Evolucion diaria hospitalaria" })).toBeVisible();
  const dailySheetCard = page.getByRole("article").filter({ hasText: "Evolucion diaria 2026-06-20" });
  await expect(dailySheetCard).toBeVisible();
  await expect(dailySheetCard.getByText("Borrador")).toBeVisible();
  await expect(page.getByText("Hoja diaria demo para validar flujo hospitalizado")).toBeVisible();
  await expect(page.getByRole("link", { name: "Editar" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar evolucion diaria" })).toBeDisabled();

  await page.getByRole("link", { name: "Editar" }).click();
  await expect(page.getByRole("heading", { name: "Editar evolucion diaria" })).toBeVisible();
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
  await expect(page.getByText("Ejecucion bloqueada")).toBeVisible();
  await expect(
    page.getByText("Requiere orden firmada, doble chequeo, MAR activo, registro de administracion y auditoria de ejecucion."),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Imprimir", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cerrar borrador" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Guardar borrador" })).toBeDisabled();
  await expect(page.getByText("Atencion ambulatoria")).toHaveCount(0);
  await expect(page.getByText("Preconsulta ambulatoria")).toHaveCount(0);
  await expect(page.getByText("workflow_kind")).toHaveCount(0);
  await expect(page.getByText("ClinicalEncounter")).toHaveCount(0);
});

test("ambulatory agenda renders persisted appointment workflow", async ({ page }) => {
  await page.goto("/consulta/agenda");

  await expect(page.getByRole("heading", { name: "Agenda", exact: true })).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Navegacion ambulatorio" });
  await expect(nav.getByRole("link", { name: "Consultas" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Agenda" })).toBeVisible();
  await expect(nav.getByText("Camas", { exact: true })).toHaveCount(0);
  await expect(nav.getByText("Evolucion diaria", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Agenda ambulatoria persistida")).toBeVisible();
  await expect(page.getByText("Control ambulatorio demo")).toBeVisible();
  await expect(page.getByText("Programada", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir atencion" }).first()).toBeVisible();
  await expect(page.getByText("Nueva cita")).toBeVisible();
  await expect(page.getByLabel("Paciente de la cita")).toContainText("Paciente Demo Alfa");
  await expect(page.getByRole("button", { name: "Guardar cita" })).toBeDisabled();
});

test("ambulatory home renders operational entry without hospital navigation", async ({ page }) => {
  await page.goto("/consulta");
  const main = page.getByRole("main");

  await expect(page.getByRole("heading", { name: "Consultas ambulatorias" })).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Navegacion ambulatorio" });
  await expect(nav.getByRole("link", { name: "Consultas" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Agenda" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Seleccionar paciente" })).toBeVisible();
  await expect(nav.getByText("Camas", { exact: true })).toHaveCount(0);
  await expect(nav.getByText("Epicrisis", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Agenda ambulatoria" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Atencion clinica" })).toBeVisible();
  await expect(page.getByText("La consulta no activa receta valida")).toBeVisible();
  await expect(main.getByText("Hospitalizacion")).toBeVisible();
  await expect(main.getByText("Se trabaja en su propia estacion.")).toBeVisible();
  await expect(page.getByText("Paciente Demo Alfa")).toHaveCount(0);
  await expect(page.getByText("Hospitalizacion demo")).toHaveCount(0);
  await expect(page.getByText("Ingreso sin cama demo")).toHaveCount(0);
  await expect(page.getByText("Indicaciones hospitalarias")).toHaveCount(0);
  await expect(page.getByText("workflow_kind")).toHaveCount(0);
  await expect(page.getByText("ClinicalEncounter")).toHaveCount(0);
});

test("ambulatory visit renders linked encounter workspace", async ({ page }) => {
  await page.goto(`/consulta/pacientes/${demoPatientId}/atencion`);

  await expect(page.getByRole("heading", { name: "Atencion ambulatoria" })).toBeVisible();
  await expect(page.getByText("Atencion clinica ambulatoria con evolucion vinculada.")).toBeVisible();
  await expect(page.getByText("Canon ambulatorio")).toHaveCount(0);
  await expect(page.getByText("Nota clinica libre")).toBeVisible();
  await expect(page.getByText("SOAP detallado (opcional)")).toBeVisible();
  await expect(page.getByText("Encuentro demo").first()).toBeVisible();
  await expect(page.getByText("Control clinico demo")).toBeVisible();
  await expect(page.getByText("Preconsulta ambulatoria")).toBeVisible();
  await expect(page.getByText("Check-in clinico minimo")).toBeVisible();
  await expect(page.getByLabel("Cita para preconsulta")).toContainText(
    "Control ambulatorio demo",
  );
  await expect(page.getByRole("button", { name: "Registrar preconsulta" })).toBeDisabled();
  await expect(page.getByText("No emite diagnostico, receta, orden ni firma.")).toBeVisible();
  await expect(page.getByText("Cierre de consulta")).toBeVisible();
  await expect(page.getByText("Atenciones en curso")).toBeVisible();
  await expect(page.getByText("Destino")).toBeVisible();
  await expect(page.getByText("completed + ended_at")).toBeVisible();
  await expect(page.getByText("no firmado")).toBeVisible();
  await expect(page.getByText("Al cerrar se guardara fecha de termino y auditoria backend.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Cerrar atencion" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Guardar atencion" })).toBeDisabled();
  await expect(page.getByText("Ingreso medico hospitalario")).toHaveCount(0);
  await expect(page.getByText("Indicaciones hospitalarias")).toHaveCount(0);
  await expect(page.getByText("Epicrisis")).toHaveCount(0);
  await expect(page.getByText("workflow_kind")).toHaveCount(0);
  await expect(page.getByText("ClinicalEncounter")).toHaveCount(0);
});

test("ambulatory domain navigation is isolated on desktop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium", "desktop sidebar only");

  await page.goto(`/consulta/pacientes/${demoPatientId}/atencion`);

  const nav = page.getByRole("navigation", { name: "Navegacion ambulatoria" });
  await expect(nav).toBeVisible();
  await expect(nav.getByRole("link", { name: "Atencion clinica" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Resumen" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Agenda" })).toBeVisible();
  await expect(nav.getByText("Ingreso", { exact: true })).toHaveCount(0);
  await expect(nav.getByText("Epicrisis", { exact: true })).toHaveCount(0);
  await expect(nav.getByText("Indicaciones", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Nueva SOAP" })).toHaveCount(0);
});

test("ambulatory summary renders real read-only patient context", async ({ page }) => {
  await page.goto(`/consulta/pacientes/${demoPatientId}/resumen`);

  await expect(page.getByRole("heading", { name: "Resumen ambulatorio" })).toBeVisible();
  await expect(page.getByText("Lectura de apoyo para la atencion clinica ambulatoria")).toBeVisible();
  await expect(page.getByText("Snapshot ambulatorio")).toBeVisible();
  await expect(page.getByText("Problema demo activo")).toBeVisible();
  await expect(page.getByText("Control ambulatorio demo")).toBeVisible();
  await expect(page.getByText("No emite receta valida")).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir atencion" })).toBeVisible();
  await expect(page.getByText("Hospitalizacion demo")).toHaveCount(0);
  await expect(page.getByText("Ingreso sin cama demo")).toHaveCount(0);
  await expect(page.getByText("Indicaciones hospitalarias")).toHaveCount(0);
  await expect(page.getByText("workflow_kind")).toHaveCount(0);
  await expect(page.getByText("ClinicalEncounter")).toHaveCount(0);
});

test("patient documents render paper index and blocked future documents", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/documentos`);
  await expect(page.getByText("Documentos y papel")).toBeVisible();
  await expect(page.getByText("Ficha clinica")).toBeVisible();
  await expect(page.getByText("Resumen paciente")).toBeVisible();
  await expect(page.getByText("Control clinico demo")).toBeVisible();
  await expect(page.getByText("Ingreso administrativo demo")).toBeVisible();
  await expect(page.getByText("Receta valida")).toBeVisible();
  await expect(page.getByText("Requiere firma, folio, actor, fecha clinica y permisos.")).toBeVisible();
  await expect(page.getByText("Adjuntos externos", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Requiere almacenamiento documental, tipo, virus scan, PHI policy, retencion y trazabilidad."),
  ).toBeVisible();
  await expect(page.getByText("Consentimientos", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Requiere plantilla versionada, firmante, fecha, custodia y revocacion."),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Ver papel" }).first()).toBeVisible();
});

test("SOAP editor exposes local assisted review without autosave", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/evoluciones/nueva`);

  await expect(page.getByRole("heading", { name: "Nueva evolucion SOAP" })).toBeVisible();
  const encounterSelect = page.locator('select[name="encounter_id"]');
  await expect(encounterSelect).toContainText("Encuentro demo - ambulatory");
  await expect(page.getByRole("button", { name: "Revisar con apoyo local" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar borrador" })).toBeVisible();
  await expect(page.getByText("Revision Ollama")).toHaveCount(0);
  await expect(page.getByText(/Borrador IA/)).toHaveCount(0);
  await expect(page.getByText(/Ollama activo|Ollama pendiente/)).toHaveCount(0);
});

test("AI settings and print routes render", async ({ page }) => {
  await page.goto("/configuracion/ia");
  await expect(page.getByRole("heading", { name: "IA local", exact: true })).toBeVisible();
  await expect(page.getByText("Estado IA local")).toBeVisible();
  await expect(page.getByText("Estado Ollama")).toHaveCount(0);
  await expect(page.getByText("IA externa")).toBeVisible();
  await expect(
    page.getByText("Requiere anonimizar payload, preview humano, autorizacion explicita, auditoria y politica PHI."),
  ).toBeVisible();

  await page.goto(`/print/pacientes/${demoPatientId}/ficha`);
  await expect(page.getByRole("heading", { name: "Ficha clinica" })).toBeVisible();
  await expect(page.getByText("Vista papel")).toBeVisible();
  await expect(page.getByText("Documento de desarrollo / no uso clinico real.")).toBeVisible();
  await expect(page.getByText("sugerencias asistidas")).toBeVisible();
  await expect(page.getByText("sugerencias Ollama")).toHaveCount(0);

  await page.goto(`/print/hospitalizacion/pacientes/${demoPatientId}/ingreso/${demoIntakeEntryId}`);
  await expect(page.getByRole("heading", { name: "Ingreso medico hospitalario" })).toBeVisible();
  await expect(page.getByText("Ingreso administrativo demo")).toBeVisible();

  await page.goto(
    `/print/hospitalizacion/pacientes/${demoHospitalizedPatientId}/epicrisis/${demoDischargeSummaryEntryId}`,
  );
  await expect(page.getByRole("heading", { name: "Alta y epicrisis" })).toBeVisible();
  await expect(page.getByText("Epicrisis preliminar demo")).toBeVisible();
});

test("login route renders local auth form", async ({ page }) => {
  await page.goto("/login");

  await expect(page.getByRole("heading", { name: "Ingresar" })).toBeVisible();
  await expect(page.getByLabel("Usuario o correo")).toBeVisible();
  await expect(page.getByLabel("Contraseña")).toBeVisible();
  await expect(page.getByLabel("Usuario o correo")).toHaveValue("");
  await expect(page.getByLabel("Contraseña")).toHaveValue("");
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeDisabled();
  await expect(page.getByRole("link", { name: "Olvide mi contraseña" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Tengo mi login bloqueado" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Pacientes|Consulta|Hospitalizacion/ })).toHaveCount(0);
  await expect(page.getByText("medico@oneepis.local")).toHaveCount(0);
  await expect(page.getByText("admin@oneepis.local")).toHaveCount(0);
  await expect(page.getByText("enfermeria@oneepis.local")).toHaveCount(0);
  await expect(page.getByText("medico", { exact: true })).toHaveCount(0);
  await expect(page.getByText("admin", { exact: true })).toHaveCount(0);
  await expect(page.getByText("dev", { exact: true })).toHaveCount(0);
  await expect(page.getByText("perfil", { exact: false })).toHaveCount(0);
  await expect(page.getByText("Seleccionar rol", { exact: false })).toHaveCount(0);
  await expect(page.getByText("Roles disponibles", { exact: false })).toHaveCount(0);
  await expect(page.getByText("Ficha clinica", { exact: true })).toBeVisible();
  await expect(page.getByText(/inteligente|Ollama|IA/)).toHaveCount(0);
});

test("recovery and unlock routes render generic request forms", async ({ page }) => {
  await page.goto("/login/recuperar");
  await expect(page.getByRole("heading", { name: "Recuperar contraseña" })).toBeVisible();
  await expect(page.getByLabel("Usuario o correo")).toBeVisible();
  await expect(page.getByRole("button", { name: "Enviar solicitud" })).toBeDisabled();

  await page.goto("/login/desbloquear");
  await expect(page.getByRole("heading", { name: "Desbloquear login" })).toBeVisible();
  await expect(page.getByLabel("Usuario o correo")).toBeVisible();
  await expect(page.getByRole("button", { name: "Enviar solicitud" })).toBeDisabled();

  await page.goto("/login/desbloquear/confirmar");
  await expect(page.getByRole("heading", { name: "Confirmar desbloqueo" })).toBeVisible();
  await expect(page.getByText("El enlace de desbloqueo no esta disponible")).toBeVisible();
  await expect(page.getByRole("link", { name: /Pacientes|Consulta|Hospitalizacion/ })).toHaveCount(0);
});

test("visible clinical routes hide technical and canon copy", async ({ page }) => {
  for (const route of VISIBLE_CLINICAL_ROUTES) {
    await page.goto(route);
    const main = page.getByRole("main");
    await expect(main).toBeVisible();
    await expect(main).not.toContainText(FORBIDDEN_CLINICAL_COPY);
  }
});

test("legacy sections map redirects to hospital physical home", async ({ page }) => {
  await page.goto("/mapa");
  await expect(page).toHaveURL(/\/home$/);
});

test("root entry redirects to hospital physical home", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/home$/);
  await expect(page.getByRole("heading", { name: "Mapa del hospital" })).toBeVisible();
});

test("hospital physical home renders only hospital places without patient data", async ({ page }) => {
  await page.goto("/home");
  const main = page.getByRole("main");

  await expect(page.getByRole("heading", { name: "Mapa del hospital" })).toBeVisible();
  await expect(
    main.getByText("Selecciona el servicio o unidad donde deseas trabajar segun tus credenciales."),
  ).toBeVisible();
  await expect(main.getByRole("heading", { name: "Administracion" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Consultas ambulatorias" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Hospitalizacion" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Farmacia" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Laboratorio" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Imagenologia" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Pabellon" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Unidad de cuidados intensivos" })).toBeVisible();
  await expect(main.getByRole("button", { name: "Futuro" }).first()).toBeDisabled();
  await expect(main.getByRole("button", { name: "Bloqueado" })).toBeDisabled();
  await expect(main.getByRole("heading", { name: "Nueva evolucion" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Nueva medicacion" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Nueva alergia" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Nuevo problema" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Registrar cama" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Nueva cama" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Receta valida" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "AI-Chart" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Signos vitales" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Medicacion activa" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Documentos del paciente" })).toHaveCount(0);
  await expect(main.getByRole("heading", { name: "Dashboard" })).toHaveCount(0);
  await expect(main.getByText("Fichas visibles")).toHaveCount(0);
  await expect(main.getByText("Mesa de pacientes")).toHaveCount(0);
  await expect(main.getByText("Actividad reciente")).toHaveCount(0);
  await expect(main.getByText("Estadisticas")).toHaveCount(0);
  await expect(main.getByText("Paciente Demo Alfa")).not.toBeVisible();
  await expect(main.getByRole("heading", { name: "Enfermeria" })).toBeVisible();
  await expect(main.getByRole("heading", { name: "Archivo clinico" })).toBeVisible();
  await expect(main.getByText("Seleccionar paciente")).toHaveCount(0);

  const hrefs = await main.locator("a").evaluateAll((links) =>
    links.map((link) => link.getAttribute("href") ?? ""),
  );
  expect(hrefs.some((href) => /\[[^\]]+\]/.test(href))).toBe(false);
  expect(hrefs.some((href) => href === "/pacientes")).toBe(false);
});
