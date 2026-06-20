"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { type ReactNode, useEffect, useState } from "react";

const TEMPLATE_STORAGE_KEY = "oneepis.visualTemplate";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            retry: 1,
          },
        },
      }),
  );

  useEffect(() => {
    const savedTemplate = window.localStorage.getItem(TEMPLATE_STORAGE_KEY) ?? "clinical-sober";
    document.documentElement.dataset.template = savedTemplate;
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ThemeProvider>
  );
}

export { TEMPLATE_STORAGE_KEY };
