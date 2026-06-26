"use client";

import { useQuery } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";

import { getCurrentUser } from "@/lib/api/auth";
import { DEMO_MODE, getStoredAuthToken, subscribeAuthToken } from "@/lib/api/client";

export function useCurrentUser() {
  const token = useSyncExternalStore(subscribeAuthToken, getStoredAuthToken, () => null);
  const query = useQuery({
    queryKey: ["auth", "me", token],
    queryFn: getCurrentUser,
    enabled: !DEMO_MODE,
    staleTime: 60_000,
    retry: false,
  });
  const session = token ?? (query.data || query.isLoading ? "active" : null);

  return {
    token: session,
    user: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
