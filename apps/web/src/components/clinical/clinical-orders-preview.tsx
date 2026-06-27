"use client";

import { useQuery } from "@tanstack/react-query";

import { ClinicalSectionCard } from "@/components/clinical/cards";
import { formatDateTime } from "@/components/clinical/date-format";
import { EmptyState, ErrorState, LoadingRows } from "@/components/clinical/states";
import { Badge } from "@/components/ui/badge";
import { listClinicalOrders } from "@/lib/api/clinical-record";
import { DEMO_MODE } from "@/lib/api/client";
import type { ClinicalOrder, ClinicalOrderStatus } from "@/lib/types";

export function ClinicalOrdersDraftPanel({ patientId }: { patientId: string }) {
  const ordersQuery = useQuery({
    queryKey: ["clinical-orders", patientId, "ficha-preview"],
    queryFn: () => listClinicalOrders(patientId, 10),
    enabled: !DEMO_MODE,
  });

  return (
    <ClinicalSectionCard
      title="Ordenes clinicas"
      description="Borradores visibles de laboratorio, imagen o enfermeria; no ejecutables ni firmados."
    >
      <ClinicalOrderDraftLegend />
      {DEMO_MODE ? (
        <EmptyState
          title="Ordenes disponibles con API real"
          description="Borrador, no ejecutable, no firmado. La ficha demo no simula ordenes persistidas."
        />
      ) : null}
      {ordersQuery.isLoading ? <LoadingRows rows={2} /> : null}
      {ordersQuery.isError ? (
        <ErrorState
          description="No se pudieron cargar ordenes clinicas."
          onRetry={() => ordersQuery.refetch()}
        />
      ) : null}
      {ordersQuery.data ? <ClinicalOrderDraftList orders={ordersQuery.data} /> : null}
    </ClinicalSectionCard>
  );
}

function ClinicalOrderDraftLegend() {
  return (
    <div className="mb-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
      <Badge variant="secondary">Borrador</Badge>
      <Badge variant="outline">No ejecutable</Badge>
      <Badge variant="outline">No firmado</Badge>
    </div>
  );
}

function ClinicalOrderDraftList({ orders }: { orders: ClinicalOrder[] }) {
  if (orders.length === 0) {
    return (
      <EmptyState
        title="Sin ordenes registradas"
        description="Las ordenes borrador apareceran aqui con su estado y fuente API."
      />
    );
  }

  return (
    <div className="space-y-2">
      {orders.map((order) => (
        <div key={order.id} className="rounded-md border bg-background p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-sm font-medium">{order.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(order.ordered_at)}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{order.kind}</Badge>
              <ClinicalOrderStatusBadges status={order.status} />
            </div>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{order.order_text}</p>
          {order.rationale ? (
            <p className="mt-2 text-xs text-muted-foreground">Motivo: {order.rationale}</p>
          ) : null}
          <p className="mt-2 break-all text-[11px] text-muted-foreground">
            Fuente: /api/v1/patients/{order.patient_id}/clinical-orders/{order.id}
          </p>
        </div>
      ))}
    </div>
  );
}

function ClinicalOrderStatusBadges({ status }: { status: ClinicalOrderStatus }) {
  if (status === "draft") {
    return (
      <>
        <Badge variant="secondary">Borrador</Badge>
        <Badge variant="outline">No ejecutable</Badge>
        <Badge variant="outline">No firmado</Badge>
      </>
    );
  }
  if (status === "cancelled") {
    return <Badge variant="warning">Anulada</Badge>;
  }
  return <Badge variant="warning">Registrada en error</Badge>;
}
