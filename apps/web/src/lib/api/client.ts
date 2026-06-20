export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const API_ACTOR = process.env.NEXT_PUBLIC_ONEEPIS_ACTOR ?? "web.dev";
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-OneEpis-Actor": API_ACTOR,
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function readErrorDetail(response: Response) {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    return `API request failed: ${response.status} ${response.statusText}`;
  }

  return `API request failed: ${response.status} ${response.statusText}`;
}
