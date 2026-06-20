"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LogIn, LogOut, ShieldCheck } from "lucide-react";
import { useSyncExternalStore } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getCurrentUser } from "@/lib/api/auth";
import {
  DEMO_MODE,
  getStoredAuthToken,
  setStoredAuthToken,
  subscribeAuthToken,
} from "@/lib/api/client";

export function SessionButton({ compact = false }: { compact?: boolean }) {
  const queryClient = useQueryClient();
  const token = useSyncExternalStore(subscribeAuthToken, getStoredAuthToken, () => null);
  const userQuery = useQuery({
    queryKey: ["auth", "me", token],
    queryFn: getCurrentUser,
    enabled: Boolean(token) && !DEMO_MODE,
    staleTime: 60_000,
    retry: false,
  });

  if (DEMO_MODE) {
    return <Badge variant="outline">Demo</Badge>;
  }

  if (!token || userQuery.isError) {
    return (
      <Button asChild variant="outline" size="sm" className={compact ? "" : "w-full justify-start"}>
        <Link href="/login">
          <LogIn className="h-4 w-4" />
          Ingresar
        </Link>
      </Button>
    );
  }

  const user = userQuery.data;
  return (
    <div className={compact ? "flex items-center gap-2" : "space-y-2"}>
      <Badge variant="safe" className="max-w-full truncate">
        <ShieldCheck className="mr-1 h-3 w-3" />
        {user ? `${user.name} - ${user.roles.join(", ")}` : "Sesion activa"}
      </Badge>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className={compact ? "" : "w-full justify-start"}
        onClick={() => {
          setStoredAuthToken(null);
          queryClient.removeQueries({ queryKey: ["auth"] });
        }}
      >
        <LogOut className="h-4 w-4" />
        Salir
      </Button>
    </div>
  );
}
