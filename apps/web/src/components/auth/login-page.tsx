"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ClipboardList, LogIn } from "lucide-react";
import { useState } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { loginLocal } from "@/lib/api/auth";
import { setStoredAuthToken } from "@/lib/api/client";

export function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const mutation = useMutation({
    mutationFn: () => loginLocal({ email, password }),
    onSuccess: () => {
      setStoredAuthToken("active");
      router.push("/home");
    },
  });
  const isLocked = mutation.error instanceof ApiError && mutation.error.status === 423;

  return (
    <main className="min-h-screen bg-background p-4 md:p-6">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-md flex-col justify-center gap-5">
        <div className="flex items-center justify-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ClipboardList className="h-5 w-5" />
          </span>
          <span>
            <span className="block text-sm font-semibold">OneEpis</span>
            <span className="block text-xs text-muted-foreground">Ficha clinica</span>
          </span>
        </div>

        <AuthCard
          title="Ingresar"
          description="Acceso privado a secciones clinicas autorizadas."
        >
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="email">Usuario o correo</Label>
              <Input
                id="email"
                type="text"
                autoComplete="username"
                value={email}
                aria-describedby={mutation.isError ? "login-error" : undefined}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                aria-describedby={mutation.isError ? "login-error" : undefined}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            <Button
              type="submit"
              className="w-full"
              disabled={mutation.isPending || !email.trim() || !password.trim()}
            >
              <LogIn className="h-4 w-4" />
              {mutation.isPending ? "Ingresando..." : "Ingresar"}
            </Button>
          </form>
          <div className="mt-4 flex flex-col gap-2 text-sm sm:flex-row sm:items-center sm:justify-between">
            <Link className="font-medium text-primary underline-offset-4 hover:underline" href="/login/recuperar">
              Olvide mi contraseña
            </Link>
            <Link className="font-medium text-primary underline-offset-4 hover:underline" href="/login/desbloquear">
              Tengo mi login bloqueado
            </Link>
          </div>
          {mutation.isError ? (
            <div id="login-error" className="mt-4" aria-live="polite">
              <ErrorState
                description={
                  isLocked
                    ? "Credenciales invalidas o cuenta no disponible. Si el bloqueo persiste, solicita desbloqueo."
                    : "Credenciales invalidas o cuenta no disponible."
                }
              />
            </div>
          ) : null}
        </AuthCard>
      </div>
    </main>
  );
}
