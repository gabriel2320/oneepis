"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ClipboardList, LoaderCircle, ShieldCheck } from "lucide-react";
import { useEffect, useRef } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { confirmUnlock } from "@/lib/api/auth";

export function UnlockConfirmPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token")?.trim() ?? "";
  const submittedToken = useRef<string | null>(null);
  const mutation = useMutation({
    mutationFn: (currentToken: string) => confirmUnlock({ token: currentToken }),
  });

  useEffect(() => {
    if (!token || submittedToken.current === token) {
      return;
    }
    submittedToken.current = token;
    mutation.mutate(token);
  }, [mutation, token]);

  const message = !token
    ? "El enlace de desbloqueo no esta disponible. Solicita un nuevo desbloqueo desde el login."
    : mutation.isPending
      ? "Validando solicitud de desbloqueo..."
      : "Solicitud procesada. Si el enlace estaba vigente, el bloqueo temporal fue levantado.";

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
        <AuthCard
          title="Confirmar desbloqueo"
          description="Procesa el enlace institucional sin revelar informacion de la cuenta."
        >
          <div
            className="rounded-md border bg-muted/20 p-3 text-sm text-muted-foreground"
            aria-live="polite"
          >
            <span className="inline-flex items-center gap-2">
              {mutation.isPending ? (
                <LoaderCircle className="h-4 w-4 animate-spin" />
              ) : (
                <ShieldCheck className="h-4 w-4" />
              )}
              {message}
            </span>
          </div>
          <Button asChild className="mt-4 w-full">
            <Link href="/login">Volver a ingresar</Link>
          </Button>
        </AuthCard>
      </div>
    </main>
  );
}
