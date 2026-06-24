"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { ClipboardList, KeyRound, LockKeyhole, LogIn, ShieldCheck, UsersRound } from "lucide-react";
import { useState } from "react";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { ErrorState } from "@/components/clinical/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginLocal } from "@/lib/api/auth";
import { setStoredAuthToken } from "@/lib/api/client";

type LocalUserPreset = {
  label: string;
  email: string;
  password: string;
  role: string;
  scope: string;
};

const localUsers: LocalUserPreset[] = [
  {
    label: "Admin dev",
    email: "admin@oneepis.local",
    password: "admin",
    role: "admin, dev",
    scope: "Gobierno completo, configuracion local y acciones clinicas.",
  },
  {
    label: "Medico",
    email: "medico@oneepis.local",
    password: "medico",
    role: "medico",
    scope: "Evoluciones SOAP, problemas, medicacion, IA clinica y encuentros.",
  },
  {
    label: "Enfermeria",
    email: "enfermeria@oneepis.local",
    password: "enfermeria",
    role: "enfermeria",
    scope: "Lectura, signos vitales y eventos clinicos longitudinales.",
  },
  {
    label: "Solo lectura",
    email: "lector@oneepis.local",
    password: "lector",
    role: "solo_lectura",
    scope: "Consulta de ficha y auditoria sin escritura clinica.",
  },
];

const permissionRows = [
  ["Leer ficha", "admin, medico, enfermeria, solo_lectura, dev"],
  ["Crear paciente y editar estado", "admin, medico, dev"],
  ["SOAP, problemas, alergias, medicacion", "admin, medico, dev"],
  ["Signos vitales y eventos", "admin, medico, enfermeria, dev"],
  ["AI-Chart y ClinicalPatch", "admin, medico, dev"],
  ["Auditoria visible", "roles autenticados con acceso a paciente"],
];

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
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl flex-col justify-center gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link href="/pacientes" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <ClipboardList className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-semibold">OneEpis</span>
              <span className="block text-xs text-muted-foreground">
                Acceso local para ficha medica
              </span>
            </span>
          </Link>
          <span className="rounded-md border px-2 py-1 text-xs text-muted-foreground">
            desarrollo sin PHI
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(320px,0.85fr)_minmax(0,1.15fr)]">
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

            <div className="mt-5 rounded-md border bg-muted/30 p-3">
              <div className="flex items-center gap-2 text-sm font-medium">
                <KeyRound className="h-4 w-4" />
                Credenciales locales
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Solo sirven para desarrollo. En entornos compartidos cambia `ONEEPIS_AUTH_SECRET`
                y `ONEEPIS_AUTH_LOCAL_USERS`.
              </p>
            </div>
          </ClinicalSectionCard>

          <div className="grid gap-4">
            <ClinicalSectionCard
              title="Tipos de usuario"
              description="Selecciona un perfil local para probar permisos por rol."
              action={<UsersRound className="h-5 w-5 text-muted-foreground" />}
            >
              <div className="grid gap-2 sm:grid-cols-2">
                {localUsers.map((user) => (
                  <button
                    key={user.email}
                    type="button"
                    className="rounded-md border bg-background p-3 text-left text-sm transition-colors hover:bg-muted"
                    onClick={() => {
                      setEmail(user.email);
                      setPassword(user.password);
                    }}
                  >
                    <span className="block font-medium text-foreground">{user.label}</span>
                    <span className="mt-1 block text-xs text-muted-foreground">{user.email}</span>
                    <span className="mt-2 block text-xs text-muted-foreground">
                      Rol: {user.role}
                    </span>
                    <span className="mt-1 block text-xs text-muted-foreground">
                      Clave local: {user.password}
                    </span>
                    <span className="mt-2 block text-xs text-muted-foreground">{user.scope}</span>
                  </button>
                ))}
              </div>
            </ClinicalSectionCard>

            <ClinicalSectionCard
              title="Permisos clinicos"
              description="La UI deshabilita acciones, pero el backend vuelve a validar cada escritura."
              action={<ShieldCheck className="h-5 w-5 text-muted-foreground" />}
            >
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs text-muted-foreground">
                    <tr className="border-b">
                      <th className="py-2 pr-3 font-medium">Accion</th>
                      <th className="py-2 font-medium">Roles habilitados</th>
                    </tr>
                  </thead>
                  <tbody>
                    {permissionRows.map(([action, roles]) => (
                      <tr key={action} className="border-b last:border-0">
                        <td className="py-2 pr-3 text-foreground">{action}</td>
                        <td className="py-2 text-muted-foreground">{roles}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ClinicalSectionCard>

            <ClinicalSectionCard
              title="Seguridad del repositorio"
              description="Reglas minimas para una ficha medica en desarrollo temprano."
              action={<LockKeyhole className="h-5 w-5 text-muted-foreground" />}
            >
              <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                <p className="rounded-md border bg-background p-3">
                  No subir datos reales, documentos clinicos, identificadores nacionales, dumps,
                  logs con PHI ni secretos.
                </p>
                <p className="rounded-md border bg-background p-3">
                  Toda escritura clinica pasa por API, rol, actor autenticado, auditoria y contrato
                  OpenAPI.
                </p>
                <p className="rounded-md border bg-background p-3">
                  Fuera de desarrollo, el backend rechaza secreto default, usuarios default, actor
                  dev y auth desactivada.
                </p>
                <p className="rounded-md border bg-background p-3">
                  AI-Chart solo propone borradores revisables; no firma ni escribe ficha sin
                  confirmacion humana.
                </p>
              </div>
            </ClinicalSectionCard>
          </div>
        </div>
      </div>
    </main>
  );
}
