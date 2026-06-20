"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ClipboardList, LogIn } from "lucide-react";
import { useState } from "react";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginLocal } from "@/lib/api/auth";
import { setStoredAuthToken } from "@/lib/api/client";

export function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("medico@oneepis.local");
  const [password, setPassword] = useState("medico");
  const mutation = useMutation({
    mutationFn: () => loginLocal({ email, password }),
    onSuccess: (response) => {
      setStoredAuthToken(response.access_token);
      router.push("/pacientes");
    },
  });

  return (
    <main className="min-h-screen bg-background p-4 md:p-6">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-md flex-col justify-center gap-5">
        <Link href="/pacientes" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ClipboardList className="h-5 w-5" />
          </span>
          <span>
            <span className="block text-sm font-semibold">OneEpis</span>
            <span className="block text-xs text-muted-foreground">Sesion local</span>
          </span>
        </Link>

        <ClinicalSectionCard
          title="Ingresar"
          description="Autenticacion local de desarrollo para auditoria y roles."
        >
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Clave</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
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
          {mutation.isError ? (
            <div className="mt-4">
              <ErrorState description="No se pudo iniciar sesion local." />
            </div>
          ) : null}
        </ClinicalSectionCard>
      </div>
    </main>
  );
}
