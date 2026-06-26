"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/components/auth/use-current-user";
import { PatientClinicalLoading } from "@/components/clinical/patient-clinical-shell";
import { DEMO_MODE } from "@/lib/api/client";

export default function Home() {
  const router = useRouter();
  const { token, isLoading, isError } = useCurrentUser();

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (!DEMO_MODE && (!token || isError)) {
      router.replace("/login");
      return;
    }
    router.replace("/home");
  }, [isError, isLoading, router, token]);

  return <PatientClinicalLoading />;
}
