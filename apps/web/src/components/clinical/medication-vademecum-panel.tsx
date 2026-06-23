"use client";

import { useState } from "react";
import { GripVertical, Search, ShieldAlert, Star } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import {
  AddMedicationButton,
  MedicationHistory,
  MedicationShortcutList,
} from "@/components/clinical/medication-vademecum-actions";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getMedicationDraftingContext,
  listMedicationCatalog,
} from "@/lib/api/medication";
import { DEMO_MODE } from "@/lib/api/client";
import type { MedicationCatalogItem } from "@/lib/types";

const FAVORITES_KEY = "oneepis.medicationFavorites.v1";

export function MedicationVademecumPanel({
  patientId,
  canWrite,
}: {
  patientId: string;
  canWrite: boolean;
}) {
  const [query, setQuery] = useState("");
  const [favoriteIds, setFavoriteIds] = useState<string[]>(readFavoriteIds);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  function updateFavorites(nextFavorites: string[]) {
    setFavoriteIds(nextFavorites);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(FAVORITES_KEY, JSON.stringify(nextFavorites));
    }
  }

  const catalogQuery = useQuery({
    queryKey: ["medication-catalog", query],
    queryFn: () => listMedicationCatalog(query),
    enabled: !DEMO_MODE,
    staleTime: 60_000,
  });
  const contextQuery = useQuery({
    queryKey: ["medication-drafting-context", patientId],
    queryFn: () => getMedicationDraftingContext(patientId),
    enabled: !DEMO_MODE,
    staleTime: 60_000,
  });

  const catalog = catalogQuery.data ?? [];
  const context = contextQuery.data;
  const selected = catalog.find((item) => item.id === selectedId) ?? catalog[0] ?? null;
  const favorites = catalog.filter((item) => favoriteIds.includes(item.id));
  const suggested = mergeCatalogItems(context?.suggested_catalog_items ?? [], catalog);

  return (
    <div className="space-y-4">
      <ClinicalSectionCard
        title="Vademecum"
        description="Catalogo local curado; no consulta FDA/openFDA en vivo."
      >
        <div className="space-y-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              value={query}
              placeholder="Buscar medicamento"
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          {catalogQuery.isLoading ? <LoadingRows rows={3} /> : null}
          {catalogQuery.isError ? (
            <ErrorState
              description="No se pudo cargar el vademecum."
              onRetry={() => catalogQuery.refetch()}
            />
          ) : null}
          {DEMO_MODE ? (
            <EmptyState title="Vademecum no disponible en demo" description="Usa API real." />
          ) : null}
          {catalog.length > 0 ? (
            <div
              className="rounded-md border border-dashed p-2"
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                const itemId = event.dataTransfer.getData("text/plain");
                if (itemId) {
                  setSelectedId(itemId);
                }
              }}
            >
              <div className="max-h-80 space-y-2 overflow-auto pr-1">
                {catalog.map((item) => (
                  <CatalogRow
                    key={item.id}
                    item={item}
                    favorite={favoriteIds.includes(item.id)}
                    selected={item.id === selected?.id}
                    onSelect={() => setSelectedId(item.id)}
                    onFavorite={() =>
                      updateFavorites(toggleFavorite(favoriteIds, item.id))
                    }
                  />
                ))}
              </div>
            </div>
          ) : null}
          {selected ? (
            <SelectedMedicationCard item={selected} patientId={patientId} canWrite={canWrite} />
          ) : null}
        </div>
      </ClinicalSectionCard>

      <ClinicalSectionCard title="Favoritos y sugeridos">
        <MedicationShortcutList
          title="Favoritos"
          items={favorites}
          patientId={patientId}
          canWrite={canWrite}
        />
        <div className="mt-4">
          <MedicationShortcutList
            title="Sugeridos"
            items={suggested}
            patientId={patientId}
            canWrite={canWrite}
          />
        </div>
      </ClinicalSectionCard>

      <ClinicalSectionCard
        title="Historial del paciente"
        description="Borrador humano; no receta valida."
      >
        <MedicationHistory context={context} patientId={patientId} canWrite={canWrite} />
        {contextQuery.isLoading ? <LoadingRows rows={2} /> : null}
        {contextQuery.isError ? (
          <ErrorState
            description="No se pudo cargar el contexto farmacologico."
            onRetry={() => contextQuery.refetch()}
          />
        ) : null}
        {context?.previous_day_indication_texts.length ? (
          <div className="mt-4 space-y-2">
            <p className="text-xs font-semibold text-muted-foreground">Indicaciones previas</p>
            {context.previous_day_indication_texts.map((text) => (
              <div key={text} className="rounded-md border p-3 text-sm">
                <p className="line-clamp-3 text-muted-foreground">{text}</p>
                <Button
                  className="mt-2"
                  size="sm"
                  variant="outline"
                  type="button"
                  onClick={async () => {
                    await navigator.clipboard.writeText(text);
                    setCopiedText("Texto copiado para revision.");
                  }}
                >
                  Copiar texto
                </Button>
              </div>
            ))}
          </div>
        ) : null}
        {copiedText ? <p className="mt-2 text-xs text-muted-foreground">{copiedText}</p> : null}
      </ClinicalSectionCard>
    </div>
  );
}

function CatalogRow({
  item,
  favorite,
  selected,
  onSelect,
  onFavorite,
}: {
  item: MedicationCatalogItem;
  favorite: boolean;
  selected: boolean;
  onSelect: () => void;
  onFavorite: () => void;
}) {
  return (
    <button
      type="button"
      draggable
      onDragStart={(event) => event.dataTransfer.setData("text/plain", item.id)}
      onClick={onSelect}
      className={`flex w-full items-start gap-2 rounded-md border p-3 text-left text-sm ${
        selected ? "border-primary bg-primary/5" : "bg-card"
      }`}
    >
      <GripVertical className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <span className="min-w-0 flex-1">
        <span className="block font-semibold">{item.display_name}</span>
        <span className="block text-xs text-muted-foreground">
          {[item.generic_name, item.route, item.strength].filter(Boolean).join(" / ")}
        </span>
      </span>
      <span
        role="button"
        tabIndex={0}
        className="rounded-md p-1 text-muted-foreground hover:bg-muted"
        onClick={(event) => {
          event.stopPropagation();
          onFavorite();
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onFavorite();
          }
        }}
        aria-label={favorite ? "Quitar favorito" : "Agregar favorito"}
      >
        <Star className={`h-4 w-4 ${favorite ? "fill-current text-warning" : ""}`} />
      </span>
    </button>
  );
}

function SelectedMedicationCard({
  item,
  patientId,
  canWrite,
}: {
  item: MedicationCatalogItem;
  patientId: string;
  canWrite: boolean;
}) {
  const rule = item.dose_rules[0];
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{item.display_name}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Fuente: {item.source_label} · {item.review_status}
          </p>
        </div>
        <Badge variant={item.status === "available" ? "safe" : "outline"}>{item.status}</Badge>
      </div>
      {rule ? (
        <div className="mt-3 rounded-md border bg-card p-3 text-xs">
          <p className="flex items-center gap-2 font-semibold">
            <ShieldAlert className="h-4 w-4" />
            Dosis y alertas
          </p>
          <p className="mt-1 text-muted-foreground">{rule.usual_dose_text ?? "Dosis usual no curada."}</p>
          <p className="mt-1 text-muted-foreground">{rule.avoid_dose_text ?? "Dosis a evitar no curada."}</p>
          <p className="mt-1 text-muted-foreground">Fuente regla: {rule.source_label}</p>
        </div>
      ) : null}
      <AddMedicationButton item={item} patientId={patientId} canWrite={canWrite} />
    </div>
  );
}

function toggleFavorite(favoriteIds: string[], itemId: string) {
  return favoriteIds.includes(itemId)
    ? favoriteIds.filter((favoriteId) => favoriteId !== itemId)
    : [...favoriteIds, itemId];
}

function readFavoriteIds() {
  if (typeof window === "undefined") {
    return [];
  }
  const rawFavorites = window.localStorage.getItem(FAVORITES_KEY);
  if (!rawFavorites) {
    return [];
  }
  try {
    return JSON.parse(rawFavorites) as string[];
  } catch {
    return [];
  }
}

function mergeCatalogItems(preferred: MedicationCatalogItem[], catalog: MedicationCatalogItem[]) {
  const byId = new Map<string, MedicationCatalogItem>();
  for (const item of [...preferred, ...catalog]) {
    byId.set(item.id, item);
  }
  return Array.from(byId.values()).slice(0, 5);
}
