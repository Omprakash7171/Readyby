"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Clock,
  Footprints,
  MapPin,
  RefreshCw,
  ShoppingBag,
  Store,
  XCircle,
} from "lucide-react";
import { ApiError, cancelOrder, fetchOrder, fetchOrderStatus } from "@/lib/api";
import type { ApiOrder, ApiOrderStatus } from "@/lib/apiTypes";
import { cn, formatPrice } from "@/lib/format";
import { useRequireSession } from "@/context/SessionProvider";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FoodArt } from "@/components/ui/FoodArt";
import { OrderStatusBadge, OrderStatusTimeline } from "@/components/order/OrderStatus";

/** How often the lightweight status endpoint is asked while an order is live. */
const POLL_INTERVAL_MS = 10_000;

export default function OrderTrackingPage({
  params,
}: {
  params: Promise<{ orderNumber: string }>;
}) {
  const { orderNumber } = use(params);
  const session = useRequireSession();

  const [order, setOrder] = useState<ApiOrder | null>(null);
  const [live, setLive] = useState<ApiOrderStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<number | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const result = await fetchOrder(orderNumber, controller.signal);
        if (controller.signal.aborted) return;
        setOrder(result);
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        if (err instanceof ApiError && (err.isNotFound || err.isForbidden)) {
          setMissing(true);
          return;
        }
        setError(err instanceof ApiError ? err.message : "We couldn't load that order.");
      }
    })();
    return () => controller.abort();
  }, [orderNumber, session.user]);

  const status = live?.status ?? order?.status ?? null;
  const dropped = status === "REJECTED" || status === "CANCELLED";
  const settled = status === "COLLECTED" || dropped;

  /**
   * Polls the lightweight status endpoint rather than the whole order. Polling
   * stops as soon as the order reaches a final state, so a completed order
   * makes no further requests.
   */
  useEffect(() => {
    if (!session.user || !order || settled) return;
    const controller = new AbortController();

    const check = async () => {
      try {
        const result = await fetchOrderStatus(order.public_id, controller.signal);
        if (controller.signal.aborted) return;
        setLive(result);
        setLastChecked(Date.now());
      } catch {
        // A failed poll is not worth surfacing; the next tick tries again.
      }
    };

    const timer = setInterval(() => void check(), POLL_INTERVAL_MS);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [session.user, order, settled]);

  async function handleCancel() {
    if (!order || cancelling) return;
    setCancelling(true);
    setCancelError(null);
    try {
      const result = await cancelOrder(order.public_id);
      if (mounted.current) {
        setOrder(result);
        setLive(null);
      }
    } catch (err) {
      if (mounted.current) {
        setCancelError(err instanceof ApiError ? err.message : "We couldn't cancel that order.");
      }
    } finally {
      if (mounted.current) setCancelling(false);
    }
  }

  if (session.pending) return null;

  if (missing) {
    return (
      <div className="mx-auto w-full max-w-3xl px-5 py-16 sm:py-24">
        <EmptyState
          icon={<ShoppingBag className="size-6" />}
          title="We couldn't find that order"
          description="It may belong to another account, or it may have been removed."
          actionLabel="Find nearby cafés"
          actionHref="/explore"
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto w-full max-w-3xl px-5 py-16 sm:py-24">
        <p role="alert" className="text-center text-ink-500">
          {error}
        </p>
      </div>
    );
  }

  if (!order || !status) {
    return (
      <div className="mx-auto w-full max-w-3xl animate-pulse px-5 py-20">
        <div className="h-96 rounded-3xl bg-ink-100" />
      </div>
    );
  }

  const isReady = status === "READY";
  const isCollected = status === "COLLECTED";
  const canCancel = status === "PLACED" || status === "ACCEPTED";

  return (
    <div className="mx-auto w-full max-w-3xl px-5 py-8 pb-28 sm:py-12 lg:pb-16">
      <Link
        href="/orders"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 transition hover:gap-2.5 hover:text-ink-900"
      >
        <ArrowLeft className="size-4" aria-hidden />
        My orders
      </Link>

      <Card
        className={cn(
          "mt-5 overflow-hidden transition-colors duration-700",
          isReady && "border-ready-300 bg-ready-50/30",
        )}
      >
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-ink-100 px-5 py-5 sm:px-7 sm:py-6">
          <div>
            <p className="text-xs font-semibold tracking-[0.14em] text-ink-400 uppercase">
              Order
            </p>
            <p className="mt-1 font-mono text-2xl font-semibold tracking-[-0.02em] text-ink-900">
              {order.public_id}
            </p>
            <p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-ink-700">
              <Store className="size-4 text-ink-400" aria-hidden />
              {order.cafe.name}
            </p>
          </div>
          <FoodArt
            variant={order.items[0]?.art ?? "hot-cup"}
            className="size-14 rounded-2xl ring-1 ring-ink-900/5"
          />
        </div>

        <div className="grid gap-6 px-5 py-6 sm:grid-cols-3 sm:px-7">
          <div>
            <p className="text-xs font-semibold tracking-[0.12em] text-ink-400 uppercase">
              You&rsquo;ll arrive
            </p>
            <p className="mt-1.5 inline-flex items-center gap-1.5 text-lg font-semibold text-ink-900">
              <Footprints className="size-4.5 text-brand-500" aria-hidden />
              {order.arrival_time_label}
            </p>
            <p className="text-xs text-ink-400">{order.arrival_day_label}</p>
          </div>
          <div>
            <p className="text-xs font-semibold tracking-[0.12em] text-brand-600 uppercase">
              Ready by
            </p>
            <p className="mt-1.5 inline-flex items-center gap-1.5 text-lg font-semibold text-brand-700">
              <Clock className="size-4.5" aria-hidden />
              {live?.estimated_ready_time_label ?? order.estimated_ready_time_label}
            </p>
            {live?.minutes_until_arrival !== null && live?.minutes_until_arrival !== undefined ? (
              <p className="text-xs text-ink-400">
                {live.minutes_until_arrival} min until you arrive
              </p>
            ) : null}
          </div>
          <div>
            <p className="text-xs font-semibold tracking-[0.12em] text-ink-400 uppercase">
              {order.destination_label ? "Heading to" : "Total at the counter"}
            </p>
            {order.destination_label ? (
              <>
                <p className="mt-1.5 inline-flex items-center gap-1.5 text-sm font-medium text-ink-800">
                  <MapPin className="size-4 text-brand-500" aria-hidden />
                  {order.destination_label}
                </p>
                <p className="mt-1 text-lg font-semibold text-ink-900 tabular-nums">
                  {formatPrice(Number(order.subtotal))}
                </p>
              </>
            ) : (
              <p className="mt-1.5 text-lg font-semibold text-ink-900 tabular-nums">
                {formatPrice(Number(order.subtotal))}
              </p>
            )}
          </div>
        </div>

        <div
          className={cn(
            "flex items-center gap-3 border-t px-5 py-4 sm:px-7",
            isReady ? "border-ready-200 bg-ready-50" : "border-ink-100",
          )}
        >
          <span
            aria-hidden
            className={cn(
              "grid size-2.5 shrink-0 rounded-full",
              settled
                ? "bg-ink-400"
                : isReady
                  ? "animate-pulse bg-ready-500"
                  : "animate-pulse bg-brand-500",
            )}
          />
          <p className="text-xl font-semibold tracking-[-0.02em] text-ink-900 sm:text-2xl">
            {live?.status_headline ?? order.status_headline}
          </p>
          <span className="ml-auto hidden sm:block">
            <OrderStatusBadge
              status={status}
              label={live?.status_label ?? order.status_label}
            />
          </span>
        </div>

        <p
          className={cn(
            "border-t px-5 py-4 text-sm leading-relaxed sm:px-7",
            isReady
              ? "border-ready-200 bg-ready-50 font-medium text-ready-900"
              : settled
                ? "border-ink-100 bg-ink-50 text-ink-500"
                : "border-ink-100 text-ink-600",
          )}
        >
          {live?.status_message ?? order.status_message}{" "}
          {isReady ? (
            <>
              Your order number is{" "}
              <span className="font-mono font-semibold text-ink-900">{order.public_id}</span>
              .
            </>
          ) : null}
        </p>
      </Card>

      <div className="mt-6 grid gap-6 sm:grid-cols-[1fr_16rem] sm:items-start">
        <Card className="p-5 sm:p-6">
          <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">Progress</h2>
          <div className="mt-5">
            <OrderStatusTimeline status={status} steps={order.tracking_steps} />
          </div>
          {!settled ? (
            <p className="mt-4 flex items-center gap-1.5 text-xs text-ink-400">
              <RefreshCw className="size-3.5" aria-hidden />
              Updates automatically every 10 seconds
              {lastChecked ? " · last checked just now" : ""}
            </p>
          ) : null}
        </Card>

        <Card className="p-5">
          <h2 className="text-sm font-semibold tracking-[-0.01em] text-ink-900">Your items</h2>
          <ul className="mt-4 space-y-3">
            {order.items.map((line) => (
              <li key={line.id} className="flex items-center gap-3">
                <FoodArt
                  variant={line.art as never}
                  className="size-9 shrink-0 rounded-xl ring-1 ring-ink-900/5"
                />
                <span className="min-w-0 flex-1 truncate text-sm text-ink-700">
                  <span className="font-semibold text-ink-900 tabular-nums">
                    {line.quantity} ×
                  </span>{" "}
                  {line.name}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-4 border-t border-ink-100 pt-4 text-xs text-ink-400">
            {order.customer.name} · pay at the counter
          </p>
        </Card>
      </div>

      {canCancel ? (
        <Card className="mt-6 border-dashed p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-semibold tracking-[-0.01em] text-ink-900">
                Change of plan?
              </h2>
              <p className="mt-1 text-pretty text-sm text-ink-500">
                You can cancel until the café starts making it.
              </p>
            </div>
            <Button
              variant="danger"
              size="lg"
              onClick={() => void handleCancel()}
              disabled={cancelling}
            >
              <XCircle className="size-4.5" aria-hidden />
              {cancelling ? "Cancelling…" : "Cancel order"}
            </Button>
          </div>
          {cancelError ? (
            <p role="alert" className="mt-3 text-sm text-red-600">
              {cancelError}
            </p>
          ) : null}
        </Card>
      ) : null}

      {order.notes ? (
        <Card className="mt-6 p-5 sm:p-6">
          <h2 className="text-sm font-semibold tracking-[-0.01em] text-ink-900">
            Your note to the café
          </h2>
          <p className="mt-2 text-pretty text-sm leading-relaxed text-ink-600">
            {order.notes}
          </p>
        </Card>
      ) : null}

      {status === "REJECTED" ? (
        <p className="mt-8 text-center text-xs text-ink-400">
          Declined by the café
          {order.rejected_reason ? `: ${order.rejected_reason}` : "."} Nothing was
          charged.
        </p>
      ) : isCollected ? (
        <p className="mt-8 text-center text-xs text-ink-400">
          This order is complete{order.cancel_reason ? `: ${order.cancel_reason}` : "."}
        </p>
      ) : null}
    </div>
  );
}