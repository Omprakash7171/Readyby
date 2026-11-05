"use client";

import {
  Check,
  Footprints,
  MapPin,
  PackageCheck,
  Timer,
  X,
} from "lucide-react";
import type { ApiOrderSummaryRow, OrderStatus } from "@/lib/apiTypes";
import { cn, formatPrice } from "@/lib/format";
import { Button } from "@/components/ui/Button";
import { FoodArt } from "@/components/ui/FoodArt";
import { OrderStatusBadge } from "@/components/order/OrderStatus";

interface MerchantOrderCardProps {
  order: ApiOrderSummaryRow;
  onAccept: () => void;
  onDecline: () => void;
  onStart: () => void;
  onMarkReady: () => void;
  onMarkCollected: () => void;
  busy?: boolean;
}

export function MerchantOrderCard({
  order,
  onAccept,
  onDecline,
  onStart,
  onMarkReady,
  onMarkCollected,
  busy,
}: MerchantOrderCardProps) {
  const closed =
    order.status === "COLLECTED" ||
    order.status === "REJECTED" ||
    order.status === "CANCELLED";
  const minutes = order.minutes_until_arrival;

  return (
    <li
      className={cn(
        "overflow-hidden rounded-3xl border bg-white shadow-soft transition-all duration-300",
        closed ? "border-ink-100 opacity-70" : "border-ink-100",
        order.status === "READY" && "border-ready-300 ring-4 ring-ready-500/10",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-ink-100 bg-crema-50 px-4 py-3 sm:px-5">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[0.95rem] font-semibold text-ink-900">
            {order.public_id}
          </span>
          <span className="text-sm text-ink-500">{order.customer_name}</span>
        </div>
        <div className="flex items-center gap-2">
          <OrderStatusBadge status={order.status} label={order.status_label} />
        </div>
      </div>

      {/**
       * The operational core of the card: when the customer arrives and when to
       * start. Without this it is just another online order ticket. Both times
       * are computed by the API when the order was placed.
       */}
      <div className="grid grid-cols-2 gap-px bg-ink-100 sm:grid-cols-3">
        <TimingCell
          icon={Footprints}
          label="Customer arrives"
          value={order.arrival_time_label}
          hint={
            closed
              ? undefined
              : minutes === 0
                ? "Any moment now"
                : `In about ${minutes} min`
          }
          tone="brand"
        />
        <TimingCell
          icon={Timer}
          label="Start preparing"
          value={order.start_preparing_time_label}
          hint={`${order.prep_time_minutes} min prep time`}
        />
        <TimingCell
          icon={MapPin}
          label="Heading to"
          value={order.destination_label || "Not set"}
          hint="Pickup — no delivery"
          className="col-span-2 sm:col-span-1"
        />
      </div>

      <div className="grid gap-5 px-4 py-4 sm:grid-cols-[1fr_auto] sm:px-5">
        <ul className="space-y-2.5">
          {order.items_detailed.map((line) => (
            <li key={line.id} className="flex items-center gap-3">
              <FoodArt
                variant={line.art as never}
                className="size-9 shrink-0 rounded-xl ring-1 ring-ink-900/5"
              />
              <span className="text-sm font-semibold text-ink-900 tabular-nums">
                {line.quantity} ×
              </span>
              <span className="min-w-0 flex-1 truncate text-sm text-ink-700">{line.name}</span>
              <span className="text-sm text-ink-500 tabular-nums">
                {formatPrice(Number(line.line_total))}
              </span>
            </li>
          ))}
        </ul>

        <div className="flex flex-col items-start gap-1 sm:items-end sm:text-right">
          <p className="text-sm font-semibold text-ink-900 tabular-nums">
            {formatPrice(Number(order.subtotal))}
          </p>
          <p className="max-w-56 text-xs text-ink-500">{order.merchant_hint}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-end gap-2 border-t border-ink-100 px-4 py-3 sm:px-5">
        <MerchantActions
          status={order.status}
          busy={busy}
          onAccept={onAccept}
          onDecline={onDecline}
          onStart={onStart}
          onMarkReady={onMarkReady}
          onMarkCollected={onMarkCollected}
        />
      </div>
    </li>
  );
}

function TimingCell({
  icon: Icon,
  label,
  value,
  hint,
  tone = "ink",
  className,
}: {
  icon: typeof Timer;
  label: string;
  value: string;
  hint?: string;
  tone?: "ink" | "brand";
  className?: string;
}) {
  return (
    <div className={cn("bg-white px-4 py-3 sm:px-5", className)}>
      <p className="flex items-center gap-1.5 text-[0.7rem] font-semibold tracking-[0.1em] text-ink-400 uppercase">
        <Icon className="size-3.5" aria-hidden />
        {label}
      </p>
      <p
        className={cn(
          "mt-1 text-[0.98rem] font-semibold tracking-[-0.02em]",
          tone === "brand" ? "text-brand-700" : "text-ink-900",
        )}
      >
        {value}
      </p>
      {hint ? <p className="mt-0.5 text-xs text-ink-500">{hint}</p> : null}
    </div>
  );
}

interface MerchantActionsProps {
  status: OrderStatus;
  busy?: boolean;
  onAccept: () => void;
  onDecline: () => void;
  onStart: () => void;
  onMarkReady: () => void;
  onMarkCollected: () => void;
}

/**
 * Only transitions the server's state machine allows are offered. The server
 * rejects anything else with 409, so the board cannot get ahead of the model.
 */
function MerchantActions({
  status,
  busy,
  onAccept,
  onDecline,
  onStart,
  onMarkReady,
  onMarkCollected,
}: MerchantActionsProps) {
  if (status === "PLACED") {
    return (
      <>
        <Button variant="danger" size="sm" onClick={onDecline} disabled={busy}>
          <X className="size-4" aria-hidden />
          Can&rsquo;t do it
        </Button>
        <Button size="sm" onClick={onAccept} disabled={busy}>
          <Check className="size-4" aria-hidden />
          Accept order
        </Button>
      </>
    );
  }

  if (status === "ACCEPTED") {
    return (
      <Button size="sm" onClick={onStart} disabled={busy}>
        <Timer className="size-4" aria-hidden />
        Start preparing
      </Button>
    );
  }

  if (status === "PREPARING") {
    return (
      <Button variant="success" size="sm" onClick={onMarkReady} disabled={busy}>
        <PackageCheck className="size-4" aria-hidden />
        Mark as ready
      </Button>
    );
  }

  if (status === "READY") {
    return (
      <Button variant="success" size="sm" onClick={onMarkCollected} disabled={busy}>
        <Check className="size-4" aria-hidden />
        Mark as collected
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-ink-500">
        {status === "COLLECTED"
          ? "Completed"
          : status === "REJECTED"
            ? "Declined"
            : "Cancelled"}
      </span>
    </div>
  );
}