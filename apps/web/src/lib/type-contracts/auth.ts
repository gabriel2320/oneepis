import type { components } from "@contracts/openapi-types";

export type UserRole = components["schemas"]["UserRole"];

export type AuthUser = components["schemas"]["AuthUserRead"];

export type LoginRequest = components["schemas"]["LoginRequest"];

export type LoginResponse = Omit<components["schemas"]["LoginResponse"], "token_type" | "user"> & {
  token_type: "bearer";
  user: AuthUser;
};

export type AuthRequestAccepted = components["schemas"]["AuthRequestAccepted"] & {
  accepted: true;
};

export type PasswordRecoveryRequest = components["schemas"]["PasswordRecoveryRequest"];

export type UnlockRequest = components["schemas"]["UnlockRequest"];

export type UnlockConfirmationRequest = components["schemas"]["UnlockConfirmationRequest"];
