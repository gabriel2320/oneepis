import { expect, test } from "@playwright/test";

const demoPatientId = "11111111-1111-4111-8111-111111111111";
const demoHospitalizedPatientId = "12222222-2222-4222-8222-222222222222";
const demoIntakeEntryId = "61111111-1111-4111-8111-111111111111";
const demoDischargeSummaryEntryId = "62222222-2222-4222-8222-222222222222";

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
  await expect(page.getByText("Hoja clinica viva")).toBeVisible();
  await expect(page.getByText("Linea clinica longitudinal")).toBeVisible();
  await expect(page.getByText("Antecedentes clinicos")).toBeVisible();
  await expect(page.getByText("Problema demo activo")).toBeVisible();
  await expect(page.getByText("Fuentes actuales", { exact: true })).toBeVisible();
  await expect(page.getByText("Sin escritura", { exact: true })).toBeVisible();
  await expect(page.getByText("Fuentes usadas")).toBeVisible();
  await expect(page.getByText("Problema activo: 1")).toBeVisible();
  await expect(page.getByText("Alergia: 1")).toBeVisible();
  await expect(page.getByText("Medicacion activa: 1")).toBeVisible();
  await expect(page.getByText("Eventos curados: 0")).toBeVisible();
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
  await expect(page.getByText("Sugerencias Ollama")).toBeVisible();
  await expect(page.getByText(/Borrador IA/)).toBeVisible();
});

test("patient navigation groups clinical areas on desktop", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "chromium", "desktop sidebar only");

  await page.goto(`/pacientes/${demoPatientId}/ficha`);

  const nav = page.getByRole("navigation", { name: "Navegacion paciente" });
  await expect(nav.getByText("Ficha", { exact: true })).toBeVisible();
  await expect(nav.getByText("Datos", { exact: true })).toBeVisible();
  await expect(nav.getByText("IA", { exact: true })).toBeVisible();
  await expect(nav.getByText("Control", { exact: true })).toBeVisible();
  await expect(nav.getByRole("link", { name: /AI-Chart/ })).toBeVisible();
  await expect(nav.getByRole("link", { name: /Auditoria/ })).toBeVisible();
});

test("patient navigation mobile selector changes sections", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile selector only");

  await page.goto(`/pacientes/${demoPatientId}/ficha`);

  const selector = page.getByLabel("Seccion clinica");
  await expect(selector).toBeVisible();
  await selector.selectOption("problemas");
  await expect(page).toHaveURL(new RegExp(`/pacientes/${demoPatientId}/problemas$`));
  await expect(page.getByText("Problemas activos")).toBeVisible();
});

test("AI-Chart renders event proposals from written entries", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/ai-chart`);

  await expect(page.getByRole("heading", { name: "AI-Chart Core" })).toBeVisible();
  await expect(page.getByText("Leer contexto")).toBeVisible();
  await expect(page.getByText("Seleccionar evidencia")).toBeVisible();
  await expect(page.getByText("Revisar propuestas")).toBeVisible();
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

test("patient events expose curation presets for patient core", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/eventos`);

  await expect(page.getByRole("heading", { name: "Eventos clinicos" })).toBeVisible();
  await expect(page.getByText("Curaduria minima para ficha tradicional")).toBeVisible();
  await expect(page.getByRole("button", { name: "Diagnostico historico" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Procedimiento previo" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Antecedente familiar/social" })).toBeDisabled();
  await expect(page.getByText("fuente y limite visible")).toBeVisible();
});

test("patient encounters render list and creation screen", async ({ page }) => {
  await page.goto(`/pacientes/${demoPatientId}/encuentros`);

  await expect(page.getByText("Encuentro demo").first()).toBeVisible();
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
  await expect(page.getByRole("link", { name: /Ingreso/ }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Epicrisis/ }).first()).toBeVisible();
});

test("hospital admission renders governed intake draft workspace", async ({ page }) => {
  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/ingreso`);

  await expect(page.getByRole("heading", { name: "Ingreso medico hospitalario" })).toBeVisible();
  await expect(page.getByText("Borrador de ingreso")).toBeVisible();
  await expect(page.getByLabel("Hospitalizacion activa")).toContainText("Hospitalizacion demo");
  await expect(page.getByText("Sin ingreso medico registrado")).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar ingreso" })).toBeDisabled();
});

test("hospital discharge summary renders governed draft workspace", async ({ page }) => {
  await page.goto(`/hospitalizacion/pacientes/${demoHospitalizedPatientId}/epicrisis`);

  await expect(page.getByRole("heading", { name: "Alta y epicrisis" })).toBeVisible();
  await expect(page.getByText("Borrador de epicrisis")).toBeVisible();
  await expect(page.getByLabel("Hospitalizacion para epicrisis")).toContainText("Hospitalizacion demo");
  await expect(page.getByText("Epicrisis preliminar demo")).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar epicrisis" })).toBeDisabled();
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
  await expect(page.getByText("Ejecucion bloqueada")).toBeVisible();
  await expect(
    page.getByText("Requiere orden firmada, doble chequeo, MAR activo, registro de administracion y auditoria de ejecucion."),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Imprimir", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Cerrar borrador" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Guardar borrador" })).toBeDisabled();
});

test("ambulatory agenda renders persisted appointment workflow", async ({ page }) => {
  await page.goto("/consulta/agenda");

  await expect(page.getByRole("heading", { name: "Agenda", exact: true })).toBeVisible();
  await expect(page.getByText("Agenda ambulatoria persistida")).toBeVisible();
  await expect(page.getByText("Control ambulatorio demo")).toBeVisible();
  await expect(page.getByText("Programada", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir atencion" }).first()).toBeVisible();
  await expect(page.getByText("Nueva cita")).toBeVisible();
  await expect(page.getByLabel("Paciente de la cita")).toContainText("Paciente Demo Alfa");
  await expect(page.getByRole("button", { name: "Guardar cita" })).toBeDisabled();
});

test("ambulatory visit renders linked encounter workspace", async ({ page }) => {
  await page.goto(`/consulta/pacientes/${demoPatientId}/atencion`);

  await expect(page.getByRole("heading", { name: "Atencion ambulatoria" })).toBeVisible();
  await expect(page.getByText("Encuentro ambulatorio y evolucion SOAP vinculada.")).toBeVisible();
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
  await expect(page.getByText("Encuentros en curso")).toBeVisible();
  await expect(page.getByText("Destino")).toBeVisible();
  await expect(page.getByText("completed + ended_at")).toBeVisible();
  await expect(page.getByText("no firmado")).toBeVisible();
  await expect(page.getByText("Al cerrar se guardara fecha de termino y auditoria backend.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Cerrar encuentro" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Guardar atencion" })).toBeDisabled();
});

test("ambulatory summary renders real read-only patient context", async ({ page }) => {
  await page.goto(`/consulta/pacientes/${demoPatientId}/resumen`);

  await expect(page.getByRole("heading", { name: "Resumen ambulatorio" })).toBeVisible();
  await expect(page.getByText("Lectura consolidada de controles")).toBeVisible();
  await expect(page.getByText("Snapshot ambulatorio")).toBeVisible();
  await expect(page.getByText("Problema demo activo")).toBeVisible();
  await expect(page.getByText("Control ambulatorio demo")).toBeVisible();
  await expect(page.getByText("No emite receta valida")).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir atencion" })).toBeVisible();
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
  await expect(page.getByText("IA externa")).toBeVisible();
  await expect(
    page.getByText("Requiere anonimizar payload, preview humano, autorizacion explicita, auditoria y politica PHI."),
  ).toBeVisible();

  await page.goto(`/print/pacientes/${demoPatientId}/ficha`);
  await expect(page.getByRole("heading", { name: "Ficha clinica" })).toBeVisible();
  await expect(page.getByText("Vista papel")).toBeVisible();
  await expect(page.getByText("Documento de desarrollo / no uso clinico real.")).toBeVisible();

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
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Clave")).toBeVisible();
});
