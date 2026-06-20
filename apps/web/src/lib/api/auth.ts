import { apiFetch } from "@/lib/api/client";
import type { AuthUser, LoginRequest, LoginResponse } from "@/lib/types";

export function loginLocal(payload: LoginRequest) {
  return apiFetch<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser() {
  return apiFetch<AuthUser>("/api/v1/auth/me");
}
