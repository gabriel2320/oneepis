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
    enabled: Boolean(token) && !DEMO_MODE,
    staleTime: 60_000,
    retry: false,
  });

  return {
    token,
    user: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
