"use client";

import { Check } from "lucide-react";
import type { OrderStatus, TrackingStep } from "@/lib/apiTypes";
import { cn } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";

/** The order of the statuses, used to work out how far along an order is. */
const PROGRESS_ORDER: OrderStatus[] = [
  "PLACED",
  "ACCEPTED",
  "PREPARING",
  "READY",
  "COLLECTED",
];

export function statusRank(status: OrderStatus) {
  const index = PROGRESS_ORDER.indexOf(status);
  return index === -1 ? -1 : index;
}

const TONE: Record<OrderStatus, "neutral" | "brand" | "ready" | "danger"> = {
  PLACED: "brand",
  ACCEPTED: "brand",
  PREPARING: "brand",
  READY: "ready",
  COLLECTED: "neutral",
  REJECTED: "danger",
  CANCELLED: "danger",
};

export function OrderStatusBadge({
  status,
  label,
  className,
}: {
  status: OrderStatus;
  /** Always the server's own wording. */
  label: string;
  className?: string;
}) {
  return (
    <Badge tone={TONE[status]} className={className}>
      {label}
    </Badge>
  );
}

/**
 * The five-step customer timeline. Both the steps and the current status come
 * from the API, so the customer app can never disagree with the café's view.
 */
export function OrderStatusTimeline({
  status,
  steps,
  className,
}: {
  status: OrderStatus;
  steps: TrackingStep[];
  className?: string;
}) {
  const rank = statusRank(status);
  const dropped = status === "CANCELLED" || status === "REJECTED";

  if (dropped) {
    return (
      <p className={cn("text-sm text-ink-500", className)}>
        {status === "REJECTED"
          ? "The café declined this order, so there is nothing left to prepare. Nothing was charged."
          : "This order was cancelled, so there is nothing left to prepare. Nothing was charged."}
      </p>
    );
  }

  return (
    <ol className={cn("space-y-0", className)}>
      {steps.map((step, index) => {
        const stepRank = statusRank(step.status);
        const done = rank >= stepRank;
        const active = rank === stepRank && step.status !== "COLLECTED";
        const last = index === steps.length - 1;

        return (
          <li key={step.status} className="flex gap-3.5">
            <div className="flex flex-col items-center">
              <span
                aria-hidden
                className={cn(
                  "grid size-6 shrink-0 place-items-center rounded-full border-2 transition-all duration-500",
                  done
                    ? "border-ready-500 bg-ready-500 text-white"
                    : active
                      ? "border-brand-500 bg-brand-500 text-white shadow-[0_0_0_5px_rgba(225,85,46,0.15)]"
                      : "border-ink-200 bg-white text-ink-300",
                )}
              >
                {done ? (
                  <Check className="size-3.5" strokeWidth={3} />
                ) : active ? (
                  <span className="size-2 rounded-full bg-white" />
                ) : (
                  <span className="size-1.5 rounded-full bg-ink-200" />
                )}
              </span>
              {!last ? (
                <span
                  aria-hidden
                  className={cn(
                    "w-0.5 flex-1 rounded-full transition-colors duration-500",
                    done ? "bg-ready-300" : "bg-ink-200",
                  )}
                />
              ) : null}
            </div>

            <div className={cn("min-w-0 flex-1", last ? "pb-0" : "pb-5")}>
              <p
                className={cn(
                  "text-sm font-medium transition-colors duration-500",
                  active ? "text-ink-900" : done ? "text-ink-700" : "text-ink-400",
                )}
              >
                {step.label}
                {active ? (
                  <span className="ml-2 text-xs font-semibold text-brand-600">Now</span>
                ) : null}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}