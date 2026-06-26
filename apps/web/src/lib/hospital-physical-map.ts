export type HospitalLocationStatus =
  | "available"
  | "available_partial"
  | "development"
  | "blocked"
  | "future";

export type HospitalLocationAccessState =
  | "available"
  | "unauthorized"
  | "development"
  | "blocked"
  | "future";

export type HospitalLocationAccessPolicy = "patient_read" | "session" | "unavailable";

export type HospitalPhysicalZoneId =
  | "acceso"
  | "area-clinica"
  | "apoyo"
  | "gestion-control";

export type HospitalPhysicalLocation = {
  id: string;
  title: string;
  type: string;
  description: string;
  primaryRoute: string | null;
  relatedRoutes: string[];
  zone: HospitalPhysicalZoneId;
  status: HospitalLocationStatus;
  accessPolicy: HospitalLocationAccessPolicy;
  actionLabel?: string;
};

export const hospitalPhysicalZones: Array<{ id: HospitalPhysicalZoneId; title: string }> = [
  { id: "acceso", title: "Acceso hospitalario" },
  { id: "area-clinica", title: "Area clinica" },
  { id: "apoyo", title: "Apoyo diagnostico y terapeutico" },
  { id: "gestion-control", title: "Gestion documental y control" },
];

export const hospitalPhysicalLocations: HospitalPhysicalLocation[] = [
  {
    id: "admision",
    title: "Admision",
    type: "Servicio administrativo",
    description: "Ingreso administrativo inicial y orientacion del paciente.",
    primaryRoute: null,
    relatedRoutes: [],
    zone: "acceso",
    status: "future",
    accessPolicy: "unavailable",
    actionLabel: "Futuro",
  },
  {
    id: "administracion",
    title: "Administracion",
    type: "Servicio administrativo",
    description: "Configuracion institucional y estado del sistema.",
    primaryRoute: "/configuracion",
    relatedRoutes: [
      "/configuracion",
      "/configuracion/api",
      "/configuracion/apariencia",
      "/configuracion/ia",
    ],
    zone: "acceso",
    status: "available",
    accessPolicy: "session",
    actionLabel: "Entrar",
  },
  {
    id: "ambulatorio",
    title: "Consultas ambulatorias",
    type: "Servicio clinico",
    description: "Atencion ambulatoria, agenda y seguimiento clinico.",
    primaryRoute: "/consulta",
    relatedRoutes: ["/consulta", "/consulta/agenda"],
    zone: "area-clinica",
    status: "available",
    accessPolicy: "patient_read",
    actionLabel: "Entrar",
  },
  {
    id: "urgencia",
    title: "Urgencia",
    type: "Servicio clinico",
    description: "Atencion inicial no programada y priorizacion clinica.",
    primaryRoute: null,
    relatedRoutes: [],
    zone: "area-clinica",
    status: "future",
    accessPolicy: "unavailable",
    actionLabel: "Futuro",
  },
  {
    id: "hospitalizacion",
    title: "Hospitalizacion",
    type: "Servicio clinico",
    description: "Ingresos, camas, rondas y evolucion intrahospitalaria.",
    primaryRoute: "/hospitalizacion",
    relatedRoutes: [
      "/hospitalizacion",
      "/hospitalizacion/camas",
      "/hospitalizacion/rondas",
    ],
    zone: "area-clinica",
    status: "available",
    accessPolicy: "patient_read",
    actionLabel: "Entrar",
  },
  {
    id: "uci",
    title: "Unidad de cuidados intensivos",
    type: "Servicio clinico critico",
    description: "Pacientes criticos y seguimiento intensivo.",
    primaryRoute: null,
    relatedRoutes: [],
    zone: "area-clinica",
    status: "future",
    accessPolicy: "unavailable",
    actionLabel: "Futuro",
  },
  {
    id: "pabellon",
    title: "Pabellon",
    type: "Servicio quirurgico",
    description: "Procedimientos quirurgicos y coordinacion operatoria.",
    primaryRoute: null,
    relatedRoutes: [],
    zone: "area-clinica",
    status: "blocked",
    accessPolicy: "unavailable",
    actionLabel: "Bloqueado",
  },
  {
    id: "enfermeria",
    title: "Enfermeria",
    type: "Estacion clinica",
    description: "Controles y registros de enfermeria autorizados.",
    primaryRoute: "/pacientes",
    relatedRoutes: ["/consulta", "/hospitalizacion"],
    zone: "area-clinica",
    status: "available_partial",
    accessPolicy: "patient_read",
    actionLabel: "Seleccionar paciente",
  },
  {
    id: "farmacia",
    title: "Farmacia",
    type: "Servicio clinico de apoyo",
    description: "Revision de medicacion y apoyo farmacologico.",
    primaryRoute: "/pacientes",
    relatedRoutes: ["/pacientes/[patientId]/medicacion"],
    zone: "apoyo",
    status: "available_partial",
    accessPolicy: "patient_read",
    actionLabel: "Seleccionar paciente",
  },
  {
    id: "laboratorio",
    title: "Laboratorio",
    type: "Servicio diagnostico",
    description: "Resultados y registros minimos de laboratorio.",
    primaryRoute: "/pacientes",
    relatedRoutes: [],
    zone: "apoyo",
    status: "available_partial",
    accessPolicy: "patient_read",
    actionLabel: "Seleccionar paciente",
  },
  {
    id: "imagenologia",
    title: "Imagenologia",
    type: "Servicio diagnostico",
    description: "Imagenes e informes radiologicos.",
    primaryRoute: null,
    relatedRoutes: [],
    zone: "apoyo",
    status: "future",
    accessPolicy: "unavailable",
    actionLabel: "Futuro",
  },
  {
    id: "archivo",
    title: "Archivo clinico",
    type: "Servicio documental",
    description: "Documentacion clinica y proyecciones en papel.",
    primaryRoute: "/pacientes",
    relatedRoutes: ["/pacientes/[patientId]/documentos", "/print/*"],
    zone: "gestion-control",
    status: "available_partial",
    accessPolicy: "patient_read",
    actionLabel: "Seleccionar paciente",
  },
  {
    id: "auditoria-calidad",
    title: "Auditoria y calidad",
    type: "Servicio de control",
    description: "Supervision, trazabilidad y control de calidad.",
    primaryRoute: null,
    relatedRoutes: ["/pacientes/[patientId]/auditoria"],
    zone: "gestion-control",
    status: "development",
    accessPolicy: "unavailable",
    actionLabel: "En desarrollo",
  },
];
