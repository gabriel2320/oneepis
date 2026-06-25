import type {
  HospitalBed,
  HospitalDailySheet,
  HospitalIndication,
} from "@/lib/types";

export const demoHospitalBeds: HospitalBed[] = [
  {
    id: "92222222-2222-4222-8222-222222222222",
    ward: "Medicina",
    room: "301",
    bed_label: "A",
    status: "occupied",
    encounter_id: "82222222-2222-4222-8222-222222222222",
    notes: "Cama demo para tablero hospitalario.",
    created_at: "2026-06-20T08:00:00Z",
    updated_at: "2026-06-20T08:00:00Z",
  },
  {
    id: "93333333-3333-4333-8333-333333333333",
    ward: "Medicina",
    room: "302",
    bed_label: "B",
    status: "available",
    encounter_id: null,
    notes: "Disponible para asignacion demo.",
    created_at: "2026-06-20T08:30:00Z",
    updated_at: "2026-06-20T08:30:00Z",
  },
];

export const demoHospitalDailySheets: HospitalDailySheet[] = [
  {
    id: "a2222222-2222-4222-8222-222222222222",
    patient_id: "12222222-2222-4222-8222-222222222222",
    encounter_id: "82222222-2222-4222-8222-222222222222",
    status: "draft",
    sheet_date: "2026-06-20",
    clinical_summary: "Hoja diaria demo para validar flujo hospitalizado sin datos reales.",
    overnight_events: "Sin eventos criticos en esta muestra ficticia.",
    active_plan: "Mantener observacion documentada y revisar pendientes.",
    pending_tasks: "Completar signos vitales y evolucion del dia si corresponde.",
    safety_notes: "Contenido ficticio de desarrollo.",
    created_by: "profesional.demo",
    created_at: "2026-06-20T09:00:00Z",
    updated_at: "2026-06-20T09:00:00Z",
  },
];

export const demoHospitalIndications: HospitalIndication[] = [
  {
    id: "b2222222-2222-4222-8222-222222222222",
    patient_id: "12222222-2222-4222-8222-222222222222",
    encounter_id: "82222222-2222-4222-8222-222222222222",
    status: "draft",
    indicated_at: "2026-06-20T10:30:00Z",
    title: "Borrador de indicacion demo",
    indication_text: "Mantener observacion documentada y revisar cambios relevantes.",
    rationale: "Contenido ficticio para validar flujo de indicacion hospitalaria.",
    safety_notes: "No corresponde a orden firmada ni a uso clinico real.",
    created_by: "profesional.demo",
    created_at: "2026-06-20T10:30:00Z",
    updated_at: "2026-06-20T10:30:00Z",
  },
];
