"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  BellRing,
  Check,
  Clock,
  Footprints,
  MapPin,
  ShoppingBag,
} from "lucide-react";
import { ApiError, fetchOrder } from "@/lib/api";
import type { ApiOrder } from "@/lib/apiTypes";
import { formatPrice } from "@/lib/format";
import { useRequireSession } from "@/context/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FoodArt } from "@/components/ui/FoodArt";
import { OrderStatusTimeline } from "@/components/order/OrderStatus";
import { SuccessBurst } from "@/components/order/SuccessBurst";

export default function ConfirmationPage({
  params,
}: {
  params: Promise<{ orderNumber: string }>;
}) {
  const { orderNumber } = use(params);
  const session = useRequireSession();

  const [order, setOrder] = useState<ApiOrder | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const result = await fetchOrder(orderNumber, controller.signal);
        setOrder(result);
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        if (err instanceof ApiError && (err.isNotFound || err.isForbidden)) {
          setMissing(true);
          return;
        }
        setError(
          err instanceof ApiError ? err.message : "We couldn't load that order.",
        );
      }
    })();
    return () => controller.abort();
  }, [orderNumber]);

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
        <p className="mt-6 text-center">
          <Link href="/orders" className="text-sm font-semibold text-brand-600">
            Back to my orders
          </Link>
        </p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="mx-auto w-full max-w-3xl animate-pulse px-5 py-20">
        <div className="h-72 rounded-3xl bg-ink-100" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-5 py-10 sm:py-14">
      <SuccessBurst />

      <div className="text-center">
        <Badge tone="ready" className="mb-5">
          <Check className="size-3.5" strokeWidth={3} aria-hidden />
          {order.status_label}
        </Badge>
        <h1 className="text-balance text-3xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-4xl">
          {order.status_headline}
        </h1>
        <p className="mx-auto mt-3 max-w-md text-pretty text-base text-ink-500 sm:text-lg">
          Arrive at{" "}
          <span className="font-semibold text-ink-900">{order.arrival_time_label}</span>,
          collect your order and go. No queue.
        </p>
      </div>

      <Card className="mt-9 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-ink-100 bg-crema-50 px-5 py-5 sm:px-6">
          <div>
            <p className="text-xs font-semibold tracking-[0.14em] text-ink-400 uppercase">
              Order number
            </p>
            <p className="mt-1 font-mono text-2xl font-semibold tracking-[-0.02em] text-ink-900">
              {order.public_id}
            </p>
            <p className="mt-1 text-sm text-ink-500">{order.cafe.name}</p>
          </div>
          <FoodArt
            variant={order.items[0]?.art ?? "hot-cup"}
            className="size-14 rounded-2xl ring-1 ring-ink-900/5"
          />
        </div>

        {/**
         * The two times the customer actually cares about, given equal billing.
         */}
        <div className="grid grid-cols-2 gap-px bg-ink-100">
          <div className="bg-white px-5 py-4 sm:px-6">
            <p className="flex items-center gap-1.5 text-[0.7rem] font-semibold tracking-[0.1em] text-ink-400 uppercase">
              <Footprints className="size-3.5" aria-hidden />
              You&rsquo;ll arrive
            </p>
            <p className="mt-1 text-lg font-semibold tracking-[-0.02em] text-ink-900">
              {order.arrival_time_label}
            </p>
            <p className="text-xs text-ink-400">{order.arrival_day_label}</p>
          </div>
          <div className="bg-white px-5 py-4 sm:px-6">
            <p className="flex items-center gap-1.5 text-[0.7rem] font-semibold tracking-[0.1em] text-brand-600 uppercase">
              <Clock className="size-3.5" aria-hidden />
              Ready by
            </p>
            <p className="mt-1 text-lg font-semibold tracking-[-0.02em] text-brand-700">
              {order.estimated_ready_time_label}
            </p>
            <p className="text-xs text-ink-400">
              {order.prep_time_minutes} min preparation
            </p>
          </div>
        </div>

        <dl className="divide-y divide-ink-100">
          <div className="flex items-center justify-between gap-4 px-5 py-4 sm:px-6">
            <dt className="text-sm text-ink-500">Items</dt>
            <dd className="text-right text-sm font-medium text-ink-900">
              {order.items.map((line) => `${line.quantity} × ${line.name}`).join(", ")}
            </dd>
          </div>
          {order.destination_label ? (
            <div className="flex items-center justify-between gap-4 px-5 py-4 sm:px-6">
              <dt className="text-sm text-ink-500">Destination</dt>
              <dd className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-900">
                <MapPin className="size-4 text-brand-500" aria-hidden />
                {order.destination_label}
              </dd>
            </div>
          ) : null}
          <div className="flex items-center justify-between gap-4 px-5 py-4 sm:px-6">
            <dt className="text-sm text-ink-500">Total at the counter</dt>
            <dd className="text-sm font-semibold text-ink-900 tabular-nums">
              {formatPrice(Number(order.subtotal))}
            </dd>
          </div>
        </dl>
      </Card>

      <Card className="mt-6 p-5 sm:p-6">
        <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
          What happens next
        </h2>
        <div className="mt-5">
          <OrderStatusTimeline status={order.status} steps={order.tracking_steps} />
        </div>
      </Card>

      <Card className="mt-6 flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:p-6">
        <span
          aria-hidden
          className="grid size-11 shrink-0 place-items-center rounded-2xl bg-ready-50 text-ready-600"
        >
          <BellRing className="size-5" />
        </span>
        <p className="text-pretty text-sm leading-relaxed text-ink-600">
          {order.cafe.name} starts preparing around{" "}
          <strong className="text-ink-900">{order.start_preparing_time_label}</strong> so
          it&rsquo;s finished by {order.estimated_ready_time_label}. Walk in and show
          order{" "}
          <span className="font-mono font-semibold text-ink-900">{order.public_id}</span>.
        </p>
      </Card>

      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <ButtonLink href={`/orders/${order.public_id}`} size="lg" className="sm:flex-1">
          Track this order
          <ArrowRight className="size-4.5" aria-hidden />
        </ButtonLink>
        <ButtonLink href="/explore" variant="outline" size="lg" className="sm:flex-1">
          <ArrowLeft className="size-4.5" aria-hidden />
          Back to nearby cafés
        </ButtonLink>
      </div>

      <p className="mt-8 text-center text-xs text-ink-400">
        Saved to your ReadyBy account
      </p>
    </div>
  );
}