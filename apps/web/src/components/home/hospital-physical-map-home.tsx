"use client";

import { AppShell } from "@/components/layout/app-shell";
import { HospitalPhysicalLocationCard } from "@/components/home/hospital-physical-location-card";
import { HospitalPhysicalZone } from "@/components/home/hospital-physical-zone";
import {
  hospitalPhysicalLocations,
  hospitalPhysicalZones,
} from "@/lib/hospital-physical-map";
import { useCurrentUser } from "@/components/auth/use-current-user";

export function HospitalPhysicalMapHome() {
  const { user } = useCurrentUser();

  return (
    <AppShell>
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 md:p-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-normal md:text-3xl">Mapa del hospital</h1>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Selecciona el servicio o unidad donde deseas trabajar segun tus credenciales.
          </p>
        </header>

        <div className="space-y-6">
          {hospitalPhysicalZones.map((zone) => {
            const locations = hospitalPhysicalLocations.filter((location) => location.zone === zone.id);
            if (locations.length === 0) return null;

            return (
              <HospitalPhysicalZone key={zone.id} id={zone.id} title={zone.title}>
                {locations.map((location) => (
                  <HospitalPhysicalLocationCard key={location.id} location={location} user={user} />
                ))}
              </HospitalPhysicalZone>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
