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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const parsed = requestSchema.safeParse(await request.json());
  if (!parsed.success) {
    return Response.json({ detail: "Invalid clinical command payload" }, { status: 422 });
  }

  const routedIntent = await routeClinicalCommand(request, parsed.data.patientId, parsed.data.text);
  const textStream = createClinicalCommandTextStream(routedIntent);
  return createTextStreamResponse({
    textStream,
    headers: {
      "Cache-Control": "no-store",
      "X-OneEpis-AI-Boundary": "next-route-handler",
    },
  });
}

async function routeClinicalCommand(request: Request, patientId: string, text: string) {
  const headers = new Headers({ "Content-Type": "application/json" });
  const authorization = request.headers.get("Authorization");
  const actor = request.headers.get("X-OneEpis-Actor");
  if (authorization) {
    headers.set("Authorization", authorization);
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
    return routeResponseSchema.parse({
      recognized: false,
      original_text: text,
      intent_type: null,
      mode: "read",
      confidence: "low",
      explanation: "No se pudo consultar la API clinica canonica.",
      suggested_actions: [],
      fallback_options: [],
    });
  }
  return routeResponseSchema.parse(await response.json());
}

function createClinicalCommandTextStream(route: RoutedIntentPreview) {
  const events = [
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

function streamEvent(type: string, payload: Record<string, unknown>) {
  return { type, ...payload };
}
