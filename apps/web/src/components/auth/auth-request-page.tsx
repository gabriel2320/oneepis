"use client";

import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { ClipboardList, Send } from "lucide-react";
import { useState } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { requestPasswordRecovery, requestUnlock } from "@/lib/api/auth";

export function AuthRequestPage({ mode }: { mode: "recovery" | "unlock" }) {
  const [email, setEmail] = useState("");
  const mutation = useMutation({
    mutationFn: () =>
      mode === "recovery" ? requestPasswordRecovery({ email }) : requestUnlock({ email }),
  });
  const title = mode === "recovery" ? "Recuperar contraseña" : "Desbloquear login";
  const description =
    mode === "recovery"
      ? "Si la cuenta existe y esta disponible, se registrara una solicitud de recuperacion."
      : "Si la cuenta existe, se registrara una solicitud de desbloqueo.";

  return (
    <main className="min-h-screen bg-background p-4 md:p-6">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-md flex-col justify-center gap-5">
        <div className="flex items-center justify-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ClipboardList className="h-5 w-5" />
          </span>
          <span>
            <span className="block text-sm font-semibold">OneEpis</span>
            <span className="block text-xs text-muted-foreground">Acceso privado</span>
          </span>
        </div>
        <AuthCard title={title} description={description}>
          {mutation.isSuccess ? (
            <div
              className="rounded-md border bg-muted/20 p-3 text-sm text-muted-foreground"
              aria-live="polite"
            >
              Solicitud enviada. Revisa los canales institucionales configurados o contacta a tu administrador.
            </div>
          ) : (
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
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={mutation.isPending || !email.trim()}
              >
                <Send className="h-4 w-4" />
                {mutation.isPending ? "Enviando..." : "Enviar solicitud"}
              </Button>
            </form>
          )}
          {mutation.isError ? (
            <div className="mt-4" aria-live="polite">
              <ErrorState description="No se pudo registrar la solicitud. Intenta nuevamente." />
            </div>
          ) : null}
          <Link
            className="mt-4 inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline"
            href="/login"
          >
            Volver a ingresar
          </Link>
        </AuthCard>
      </div>
    </main>
  );
}
