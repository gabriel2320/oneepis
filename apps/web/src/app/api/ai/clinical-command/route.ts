import { createTextStreamResponse } from "ai";
import { z } from "zod";

export const runtime = "nodejs";

const requestSchema = z.object({
  patientId: z.string().uuid(),
  text: z.string().min(1).max(320),
});

const routeResponseSchema = z
  .object({
    recognized: z.boolean(),
    original_text: z.string(),
    intent_type: z.string().nullable().optional(),
    mode: z.string(),
    confidence: z.enum(["high", "moderate", "low"]),
    explanation: z.string(),
    suggested_actions: z.array(z.object({ label: z.string() }).passthrough()),
    fallback_options: z.array(z.object({ label: z.string() }).passthrough()),
  })
  .passthrough();

type RoutedIntentPreview = z.infer<typeof routeResponseSchema>;
type ClinicalCommandRouteResult =
  | { ok: true; route: RoutedIntentPreview }
  | { ok: false; status: number; explanation: string };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const parsed = requestSchema.safeParse(await request.json());
  if (!parsed.success) {
    return Response.json({ detail: "Invalid clinical command payload" }, { status: 422 });
  }

  const result = await routeClinicalCommand(request, parsed.data.patientId, parsed.data.text);
  const textStream = createClinicalCommandTextStream(result);
  return createTextStreamResponse({
    textStream,
    headers: {
      "Cache-Control": "no-store",
      "X-OneEpis-AI-Boundary": "next-route-handler",
    },
  });
}

async function routeClinicalCommand(
  request: Request,
  patientId: string,
  text: string,
): Promise<ClinicalCommandRouteResult> {
  const headers = new Headers({ "Content-Type": "application/json" });
  const authorization = request.headers.get("Authorization");
  const cookie = request.headers.get("Cookie");
  const csrf = csrfFromCookie(cookie);
  const actor = request.headers.get("X-OneEpis-Actor");
  if (authorization) {
    headers.set("Authorization", authorization);
  }
  if (cookie) {
    headers.set("Cookie", cookie);
  }
  if (csrf) {
    headers.set("X-OneEpis-CSRF", csrf);
  }
  if (actor) {
    headers.set("X-OneEpis-Actor", actor);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/patients/${patientId}/ai/clinical-intent-route`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ text }),
      cache: "no-store",
    },
  );
  if (!response.ok) {
    return {
      ok: false,
      status: response.status,
      explanation: `API clinica canonica respondio ${response.status}.`,
    };
  }
  return { ok: true, route: routeResponseSchema.parse(await response.json()) };
}

function csrfFromCookie(cookie: string | null) {
  if (!cookie) {
    return null;
  }
  const prefix = "oneepis_csrf=";
  const csrfCookie = cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(prefix));
  return csrfCookie ? decodeURIComponent(csrfCookie.slice(prefix.length)) : null;
}

function createClinicalCommandTextStream(result: ClinicalCommandRouteResult) {
  const events = result.ok ? successfulRouteEvents(result.route) : failedRouteEvents(result);

  return new ReadableStream<string>({
    async start(controller) {
      for (const event of events) {
        controller.enqueue(`${JSON.stringify(event)}\n`);
        await new Promise((resolve) => setTimeout(resolve, 15));
      }
      controller.close();
    },
  });
}

function successfulRouteEvents(route: RoutedIntentPreview) {
  return [
    streamEvent("status", { message: "Consultando API clinica canonica." }),
    streamEvent("proposal", { data: route }),
    streamEvent("status", {
      message: route.recognized ? "Intencion reconocida." : "Intencion no reconocida.",
    }),
    streamEvent("source", {
      sourceId: "fastapi.clinical_intent_route",
      label: "Router clinico deterministico FastAPI",
    }),
    streamEvent("status", {
      message: `Confianza ${route.confidence}; modo ${route.mode}. ${route.explanation}`,
    }),
    ...route.suggested_actions.map((action) =>
      streamEvent("status", { message: `Accion propuesta: ${action.label}` }),
    ),
    ...route.fallback_options.map((action) =>
      streamEvent("status", { message: `Opcion segura: ${action.label}` }),
    ),
    streamEvent("warning", {
      message: "No se aplicaron cambios a la ficha. Toda escritura requiere confirmacion humana.",
    }),
    streamEvent("done", {}),
  ];
}

function failedRouteEvents(result: Extract<ClinicalCommandRouteResult, { ok: false }>) {
  return [
    streamEvent("status", { message: "Consultando API clinica canonica." }),
    streamEvent("warning", {
      message: result.explanation,
      api_status: result.status,
    }),
    streamEvent("warning", {
      message: "No se aplicaron cambios a la ficha. Revise autenticacion o disponibilidad API.",
    }),
    streamEvent("done", {}),
  ];
}

function streamEvent(type: string, payload: Record<string, unknown>) {
  return { type, ...payload };
}
