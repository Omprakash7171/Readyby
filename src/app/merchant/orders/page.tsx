"use client";

import { useCallback, useEffect, useState } from "react";
import { Coffee, Inbox, RefreshCw, Store } from "lucide-react";
import {
  ApiError,
  fetchBoardSummary,
  fetchMerchantOrders,
  fetchMyCafe,
  updateOrderStatus,
} from "@/lib/api";
import type {
  ApiOrderSummaryRow,
  BoardSummary,
  MerchantCafe,
  OrderStatus,
} from "@/lib/apiTypes";
import { cn } from "@/lib/format";
import { useRequireSession } from "@/context/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { MerchantStats } from "@/components/merchant/MerchantStats";
import { MerchantOrderCard } from "@/components/merchant/MerchantOrderCard";
import { WhyReadyBy } from "@/components/merchant/WhyReadyBy";

type Filter = "all" | "new" | "preparing" | "ready" | "collected";

const FILTERS: { key: Filter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "new", label: "New" },
  { key: "preparing", label: "In progress" },
  { key: "ready", label: "Ready" },
  { key: "collected", label: "Closed" },
];

const POLL_INTERVAL_MS = 12_000;

export default function MerchantPage() {
  const session = useRequireSession(["MERCHANT", "ADMIN"]);

  const [cafe, setCafe] = useState<MerchantCafe | null>(null);
  const [orders, setOrders] = useState<ApiOrderSummaryRow[] | null>(null);
  const [summary, setSummary] = useState<BoardSummary | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  /** Bumped by a manual refresh or a status change to re-run the board load. */
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!session.user) return;
    void (async () => {
      try {
        setCafe(await fetchMyCafe());
      } catch {
        setPageError("No café is linked to this account yet.");
      }
    })();
  }, [session.user]);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();

    void (async () => {
      try {
        const [list, stats] = await Promise.all([
          fetchMerchantOrders(undefined, controller.signal),
          fetchBoardSummary(controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setOrders(list.results);
        setSummary(stats);
        setPageError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setPageError(
          err instanceof ApiError
            ? err.message
            : "We couldn't load the board. Check that the API is running.",
        );
      }
    })();

    // Poll so a customer order appears without the café refreshing by hand.
    const timer = setInterval(() => {
      setReloadToken((token) => token + 1);
    }, POLL_INTERVAL_MS);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [session.user, reloadToken]);

  const move = useCallback(
    async (publicId: string, status: OrderStatus) => {
      setBusyId(publicId);
      setActionError(null);
      try {
        await updateOrderStatus(publicId, status);
        // Patch the row straight away so the ticket never flashes its old
        // status, then pull the authoritative board behind it.
        setOrders((current) =>
          current?.map((order) =>
            order.public_id === publicId ? { ...order, status } : order,
          ) ?? current,
        );
        setReloadToken((token) => token + 1);
      } catch (err) {
        setActionError(
          err instanceof ApiError ? err.message : "That change could not be saved.",
        );
      } finally {
        setBusyId(null);
      }
    },
    [],
  );

  if (session.pending) return null;

  const visible = (orders ?? []).filter((order) => {
    if (filter === "all") return true;
    if (filter === "new") return order.status === "PLACED";
    if (filter === "preparing")
      return order.status === "ACCEPTED" || order.status === "PREPARING";
    if (filter === "ready") return order.status === "READY";
    return order.status === "COLLECTED" || order.status === "CANCELLED";
  });

  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-8 sm:py-12">
      <header className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-4">
          <span
            aria-hidden
            className="grid size-12 shrink-0 place-items-center rounded-2xl bg-ink-900 text-white"
          >
            <Coffee className="size-6" />
          </span>
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-3xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-4xl">
                {cafe?.name ?? "Your café"}
              </h1>
              {cafe?.is_demo ? <Badge tone="brand">Demo café</Badge> : null}
              {cafe?.is_active ? null : <Badge tone="danger">Inactive</Badge>}
            </div>
            <p className="mt-1.5 text-base text-ink-500">
              Pickup board — every order with the customer&rsquo;s arrival time
            </p>
            {cafe ? (
              <p className="mt-2 flex items-center gap-1.5 text-sm text-ink-400">
                <Store className="size-4" aria-hidden />
                {cafe.address}
                {cafe.postcode ? `, ${cafe.postcode}` : ""} · {cafe.prep_time_minutes} min
                prep
              </p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-col gap-2.5 sm:flex-row lg:shrink-0">
          <Button
            variant="outline"
            onClick={() => setReloadToken((token) => token + 1)}
          >
            <RefreshCw className="size-4" aria-hidden />
            Refresh
          </Button>
          <ButtonLink href="/explore" variant="dark">
            Customer view
          </ButtonLink>
        </div>
      </header>

      {pageError ? (
        <p
          role="alert"
          className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {pageError}
        </p>
      ) : null}

      {summary ? <MerchantStats summary={summary} className="mt-8" /> : null}

      {actionError ? (
        <p role="alert" className="mt-4 text-sm text-red-600">
          {actionError}
        </p>
      ) : null}

      <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_23rem] lg:items-start">
        <section aria-labelledby="order-board-heading" className="min-w-0">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2
                id="order-board-heading"
                className="text-xl font-semibold tracking-[-0.025em] text-ink-900"
              >
                Pickup orders
              </h2>
              <p className="mt-1 text-pretty text-sm text-ink-500">
                Every ticket shows when the customer arrives and when to start.
                Accept, prepare, then hand over — the customer screen updates
                itself.
              </p>
            </div>
            <nav
              aria-label="Filter orders"
              className="no-scrollbar -mx-1 flex gap-1.5 overflow-x-auto px-1"
            >
              {FILTERS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setFilter(option.key)}
                  aria-pressed={filter === option.key}
                  className={cn(
                    "shrink-0 rounded-full px-3.5 py-2 text-sm font-medium transition-colors",
                    filter === option.key
                      ? "bg-ink-900 text-white"
                      : "bg-white text-ink-600 ring-1 ring-ink-100 hover:text-ink-900",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </nav>
          </div>

          {orders === null ? (
            <ul className="mt-6 space-y-3">
              {[0, 1].map((index) => (
                <li key={index} className="h-52 animate-pulse rounded-3xl bg-ink-100" />
              ))}
            </ul>
          ) : visible.length === 0 ? (
            <div className="mt-6 flex flex-col items-center rounded-3xl border border-dashed border-ink-200 bg-white/60 px-6 py-16 text-center">
              <span
                aria-hidden
                className="grid size-14 place-items-center rounded-2xl bg-crema-100 text-ink-400"
              >
                <Inbox className="size-6" />
              </span>
              <h3 className="mt-4 text-lg font-semibold tracking-[-0.02em] text-ink-900">
                Nothing here right now
              </h3>
              <p className="mt-2 max-w-sm text-pretty text-sm leading-relaxed text-ink-500">
                No {filter === "all" ? "" : filter} orders on the board. A customer
                order will appear here within a few seconds.
              </p>
              <ButtonLink href="/explore" variant="outline" className="mt-6">
                Open the customer side
              </ButtonLink>
            </div>
          ) : (
            <ul className="mt-6 space-y-3">
              {visible.map((order) => (
                <MerchantOrderCard
                  key={order.public_id}
                  order={order}
                  busy={busyId === order.public_id}
                  onAccept={() => void move(order.public_id, "ACCEPTED")}
                  onDecline={() => void move(order.public_id, "REJECTED")}
                  onStart={() => void move(order.public_id, "PREPARING")}
                  onMarkReady={() => void move(order.public_id, "READY")}
                  onMarkCollected={() => void move(order.public_id, "COLLECTED")}
                />
              ))}
            </ul>
          )}
        </section>

        <aside className="lg:sticky lg:top-24">
          <CardCallout />
          <WhyReadyBy />
        </aside>
      </div>
    </div>
  );
}

function CardCallout() {
  return (
    <div className="mb-6 overflow-hidden rounded-3xl border border-ink-900 bg-ink-900 p-6 text-white">
      <p className="text-xs font-semibold tracking-[0.16em] text-brand-300 uppercase">
        The pitch
      </p>
      <p className="mt-3 text-pretty text-lg leading-snug font-medium tracking-[-0.02em]">
        This isn&rsquo;t just another online order. It tells you when the customer
        is walking over, so you can start the right thing at the right time.
      </p>
      <div className="mt-5 flex flex-wrap gap-2 text-xs">
        <span className="rounded-full bg-white/10 px-3 py-1.5">
          Arrival time on every ticket
        </span>
        <span className="rounded-full bg-white/10 px-3 py-1.5">Pickup only</span>
        <span className="rounded-full bg-white/10 px-3 py-1.5">No delivery run</span>
      </div>
    </div>
  );
}