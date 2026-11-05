"use client";

import { useEffect, useState } from "react";
import { ShoppingBag } from "lucide-react";
import { ApiError, fetchMyOrders } from "@/lib/api";
import type { ApiOrderSummaryRow } from "@/lib/apiTypes";
import { useRequireSession } from "@/context/SessionProvider";
import { EmptyState } from "@/components/ui/EmptyState";
import { OrderCard } from "@/components/order/OrderCard";

const CLOSED = new Set(["COLLECTED", "CANCELLED"]);

export default function OrdersPage() {
  const session = useRequireSession();
  const [orders, setOrders] = useState<ApiOrderSummaryRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const result = await fetchMyOrders(controller.signal);
        setOrders(result.results);
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setError(
          err instanceof ApiError ? err.message : "We couldn't load your orders.",
        );
      }
    })();
    return () => controller.abort();
  }, [session.user]);

  if (session.pending) return null;

  const active = (orders ?? []).filter((order) => !CLOSED.has(order.status));
  const past = (orders ?? []).filter((order) => CLOSED.has(order.status));
  const loaded = orders ?? [];

  return (
    <div className="mx-auto w-full max-w-4xl px-5 py-10 sm:py-14">
      <header>
        <p className="text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
          Your account
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-5xl">
          My orders
        </h1>
        <p className="mt-3 text-pretty text-base text-ink-500">
          Every order you&rsquo;ve placed, newest first.
        </p>
      </header>

      {error ? (
        <p role="alert" className="mt-9 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {orders === null && !error ? (
        <ul className="mt-9 space-y-3">
          {Array.from({ length: 3 }, (_, index) => (
            <li key={index} className="h-28 animate-pulse rounded-3xl bg-ink-100" />
          ))}
        </ul>
      ) : loaded.length === 0 ? (
        <EmptyState
          className="mt-9"
          icon={<ShoppingBag className="size-6" />}
          title="No orders yet"
          description="Choose a destination, order from a nearby café and it'll show up here."
          actionLabel="Find nearby cafés"
          actionHref="/explore"
        />
      ) : (
        <div className="mt-9 space-y-10">
          {active.length ? (
            <section aria-labelledby="active-orders">
              <h2
                id="active-orders"
                className="text-sm font-semibold tracking-[0.12em] text-ink-400 uppercase"
              >
                In progress
              </h2>
              <ul className="mt-4 space-y-3">
                {active.map((order) => (
                  <OrderCard key={order.public_id} order={order} />
                ))}
              </ul>
            </section>
          ) : null}

          {past.length ? (
            <section aria-labelledby="past-orders">
              <h2
                id="past-orders"
                className="text-sm font-semibold tracking-[0.12em] text-ink-400 uppercase"
              >
                Finished
              </h2>
              <ul className="mt-4 space-y-3">
                {past.map((order) => (
                  <OrderCard key={order.public_id} order={order} />
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      )}
    </div>
  );
}