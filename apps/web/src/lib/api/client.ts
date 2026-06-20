export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const API_ACTOR = process.env.NEXT_PUBLIC_ONEEPIS_ACTOR;
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
export const AUTH_TOKEN_STORAGE_KEY = "oneepis.auth.token";

const authListeners = new Set<() => void>();

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
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getStoredAuthToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (API_ACTOR && !headers.has("X-OneEpis-Actor")) {
    headers.set("X-OneEpis-Actor", API_ACTOR);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
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

export function getStoredAuthToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

export function setStoredAuthToken(token: string | null) {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  }
  authListeners.forEach((listener) => listener());
}

export function subscribeAuthToken(listener: () => void) {
  if (typeof window === "undefined") {
    return () => undefined;
  }
  authListeners.add(listener);
  const onStorage = (event: StorageEvent) => {
    if (event.key === AUTH_TOKEN_STORAGE_KEY) {
      listener();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    authListeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
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
