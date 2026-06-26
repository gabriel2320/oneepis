export type UserRole = "admin" | "medico" | "enfermeria" | "solo_lectura" | "dev";

export type AuthUser = {
  email: string;
  name: string;
  roles: UserRole[];
  actor_id: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: AuthUser;
};

export type AuthRequestAccepted = {
  accepted: true;
};

export type PasswordRecoveryRequest = {
  email: string;
};

export type UnlockRequest = {
  email: string;
};

export type UnlockConfirmationRequest = {
  token: string;
};
