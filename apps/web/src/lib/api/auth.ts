import { apiFetch } from "@/lib/api/client";
import type {
  AuthRequestAccepted,
  AuthUser,
  LoginRequest,
  LoginResponse,
  UnlockConfirmationRequest,
  PasswordRecoveryRequest,
  UnlockRequest,
} from "@/lib/types";

export function loginLocal(payload: LoginRequest) {
  return apiFetch<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser() {
  return apiFetch<AuthUser>("/api/v1/auth/me");
}

export function logoutLocal() {
  return apiFetch<AuthRequestAccepted>("/api/v1/auth/logout", {
    method: "POST",
  });
}

export function refreshLocalSession() {
  return apiFetch<LoginResponse>("/api/v1/auth/refresh", {
    method: "POST",
  });
}

export function requestPasswordRecovery(payload: PasswordRecoveryRequest) {
  return apiFetch<AuthRequestAccepted>("/api/v1/auth/password-recovery-requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function requestUnlock(payload: UnlockRequest) {
  return apiFetch<AuthRequestAccepted>("/api/v1/auth/unlock-requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function confirmUnlock(payload: UnlockConfirmationRequest) {
  return apiFetch<AuthRequestAccepted>("/api/v1/auth/unlock-confirmations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
