import Link from "next/link";
import { ArrowRight } from "lucide-react";

import {
  HospitalLocationStatusBadge,
  hospitalLocationActionText,
} from "@/components/home/hospital-location-status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { HospitalPhysicalLocation } from "@/lib/hospital-physical-map";
import { resolveHospitalLocationAccess } from "@/lib/permissions";
import type { AuthUser } from "@/lib/types";
import { cn } from "@/lib/utils";

export function HospitalPhysicalLocationCard({
  location,
  user,
}: {
  location: HospitalPhysicalLocation;
  user?: AuthUser | null;
}) {
  const accessState = resolveHospitalLocationAccess(location, user);
  const isEnabled = accessState === "available" && Boolean(location.primaryRoute);
  const actionText = hospitalLocationActionText(accessState, location.actionLabel);

  return (
    <Card
      className={cn(
        "flex h-full flex-col overflow-hidden",
        !isEnabled && "bg-muted/40 text-muted-foreground",
      )}
    >
      <article className="flex h-full flex-col">
        <CardHeader className="space-y-3">
          <div className="min-w-0 space-y-1">
            <CardTitle className="text-base leading-tight">{location.title}</CardTitle>
            <p className="text-xs font-medium text-muted-foreground">{location.type}</p>
          </div>
          <HospitalLocationStatusBadge status={location.status} accessState={accessState} />
        </CardHeader>
        <CardContent className="flex flex-1 flex-col justify-between gap-4">
          <p className="text-sm leading-6 text-muted-foreground">{location.description}</p>
          {isEnabled && location.primaryRoute ? (
            <Button asChild className="w-full justify-center">
              <Link href={location.primaryRoute}>
                {actionText}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          ) : (
            <Button className="w-full justify-center" variant="outline" disabled>
              {actionText}
            </Button>
          )}
        </CardContent>
      </article>
    </Card>
  );
}
