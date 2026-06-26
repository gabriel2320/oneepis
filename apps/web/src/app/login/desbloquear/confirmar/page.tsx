import { Suspense } from "react";

import { UnlockConfirmPage } from "@/components/auth/unlock-confirm-page";

export default function Page() {
  return (
    <Suspense>
      <UnlockConfirmPage />
    </Suspense>
  );
}
