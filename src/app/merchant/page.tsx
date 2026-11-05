"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Clock3,
  Coffee,
  PoundSterling,
  RefreshCw,
  ShoppingBag,
  Store,
  UserRound,
  UtensilsCrossed,
} from "lucide-react";
import {
  ApiError,
  fetchBoardSummary,
  fetchMerchantOrders,
  fetchMerchantPickupSlots,
  fetchMyCafe,
} from "@/lib/api";
import type {
  ApiOrderSummaryRow,
  BoardSummary,
  MerchantCafe,
  MerchantPickupSlots,
} from "@/lib/apiTypes";
import { formatPrice } from "@/lib/format";
import { useRequireSession } from "@/context/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Photo } from "@/components/ui/Photo";

const STATUS_TONE = {
  PLACED: "brand",
  ACCEPTED: "info",
  PREPARING: "warning",
  READY: "ready",
  COLLECTED: "neutral",
  REJECTED: "danger",
  CANCELLED: "neutral",
} as const;

export default function MerchantDashboardPage() {
  const session = useRequireSession(["MERCHANT", "ADMIN"]);
  const [cafe, setCafe] = useState<MerchantCafe | null>(null);
  const [summary, setSummary] = useState<BoardSummary | null>(null);
  const [orders, setOrders] = useState<ApiOrderSummaryRow[]>([]);
  const [pickup, setPickup] = useState<MerchantPickupSlots | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const [cafeData, stats, list, slots] = await Promise.all([
          fetchMyCafe(),
          fetchBoardSummary(controller.signal),
          fetchMerchantOrders(undefined, controller.signal),
          fetchMerchantPickupSlots(controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setCafe(cafeData);
        setSummary(stats);
        setOrders(list.results);
        setPickup(slots);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "We couldn't load your cafe dashboard. Check that the API is running.",
        );
      }
    })();
    return () => controller.abort();
  }, [session.user, reloadToken]);

  if (session.pending) return null;

  const recent = orders.slice(0, 5);
  const nextSlots = (pickup?.slots ?? []).slice(0, 4);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-3xl font-semibold tracking-[-0.035em] text-ink-900">
              {cafe?.name ?? "Your cafe"}
            </h1>
            {cafe?.is_demo ? <Badge tone="brand">Demo cafe</Badge> : null}
            {cafe && !cafe.is_active ? <Badge tone="danger">Inactive</Badge> : null}
          </div>
          <p className="mt-1.5 max-w-2xl text-pretty text-ink-500">
            A live view of the counter: orders, pickup pressure and the next
            arrivals.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setReloadToken((n) => n + 1)}>
            <RefreshCw className="size-4" aria-hidden />
            Refresh
          </Button>
          <ButtonLink href="/merchant/orders" variant="dark">
            Open orders
            <ArrowRight className="size-4" aria-hidden />
          </ButtonLink>
        </div>
      </header>

      {error ? (
        <p
          role="alert"
          className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </p>
      ) : null}

      <section aria-label="Today at a glance" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          icon={ShoppingBag}
          label="Orders today"
          value={summary ? String(summary.orders_today) : "-"}
          note={summary ? `${summary.pending} waiting for action` : "Loading"}
        />
        <Metric
          icon={Clock3}
          label="Pending"
          value={summary ? String(summary.pending) : "-"}
          note="New and in progress"
          tone="brand"
        />
        <Metric
          icon={PoundSterling}
          label="Pickup sales"
          value={summary ? formatPrice(Number(summary.revenue_today)) : "-"}
          note="Collected today"
          tone="ready"
        />
        <Metric
          icon={Coffee}
          label="Next slot"
          value={nextSlots[0]?.time_label ?? "-"}
          note={nextSlots[0] ? `${nextSlots[0].remaining} of ${nextSlots[0].capacity} left` : "No open slots"}
        />
      </section>

      <div className="grid gap-6 xl:grid-cols-[1fr_20rem] xl:items-start">
        <div className="space-y-6">
          <Card className="overflow-hidden">
            <div className="flex items-center justify-between gap-3 border-b border-ink-100 px-5 py-4">
              <div>
                <h2 className="font-semibold tracking-[-0.02em] text-ink-900">Recent orders</h2>
                <p className="mt-0.5 text-sm text-ink-500">The newest tickets first.</p>
              </div>
              <Link
                href="/merchant/orders"
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                View all
              </Link>
            </div>
            {recent.length === 0 ? (
              <div className="px-5 py-12 text-center">
                <p className="font-medium text-ink-800">No orders yet today</p>
                <p className="mt-1 text-sm text-ink-500">
                  New customer orders will appear here automatically.
                </p>
              </div>
            ) : (
              <ul className="divide-y divide-ink-100">
                {recent.map((order) => (
                  <li key={order.public_id} className="flex items-center gap-3 px-5 py-3.5">
                    <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-crema-100 text-ink-500">
                      <ShoppingBag className="size-4" aria-hidden />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="truncate text-sm font-semibold text-ink-900">
                          {order.customer_name}
                        </p>
                        <Badge tone={STATUS_TONE[order.status]}>{order.status_label}</Badge>
                      </div>
                      <p className="mt-0.5 truncate text-xs text-ink-500">
                        {order.items_detailed.reduce((sum, item) => sum + item.quantity, 0)} items
                        {" · "}
                        {order.arrival_time_label}
                      </p>
                    </div>
                    <span className="text-sm font-medium text-ink-800">
                      {formatPrice(Number(order.subtotal))}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold tracking-[-0.02em] text-ink-900">Upcoming pickup slots</h2>
                <p className="mt-0.5 text-sm text-ink-500">
                  Orders booked into each 15-minute window.
                </p>
              </div>
              <Link
                href="/merchant/pickup-slots"
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                Manage
              </Link>
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {nextSlots.length === 0 ? (
                <p className="text-sm text-ink-500">No bookable slots in the next 24 hours.</p>
              ) : (
                nextSlots.map((slot) => {
                  const used = slot.capacity - slot.remaining;
                  const pct = Math.min(100, Math.round((used / slot.capacity) * 100));
                  return (
                    <div key={slot.arrival_time} className="rounded-2xl bg-crema-50 p-3.5">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-ink-900">{slot.time_label}</p>
                        <span className="text-xs text-ink-500">
                          {slot.remaining}/{slot.capacity} left
                        </span>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-ink-100">
                        <div
                          className="h-full rounded-full bg-brand-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <p className="mt-1.5 text-xs text-ink-400">{slot.day_label}</p>
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </div>

        <aside className="space-y-4">
          <Card className="overflow-hidden">
            <Photo
              src={cafe?.image_url}
              alt={cafe ? `${cafe.name} interior` : "Cafe"}
              art="latte"
              banner
              className="h-36"
            />
            <div className="p-5">
              <div className="flex items-start gap-2">
                <Store className="mt-0.5 size-4 shrink-0 text-ink-400" aria-hidden />
                <div>
                  <p className="font-semibold text-ink-900">{cafe?.name ?? "Your cafe"}</p>
                  <p className="mt-1 text-sm text-ink-500">
                    {cafe?.address}
                    {cafe?.postcode ? `, ${cafe.postcode}` : ""}
                  </p>
                </div>
              </div>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-ink-400">Prep</dt>
                  <dd className="font-medium text-ink-800">{cafe?.prep_time_minutes ?? "-"} min</dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-400">Kitchen</dt>
                  <dd className="font-medium text-ink-800">{cafe?.kitchen_capacity ?? "-"} at once</dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-400">Slot cap</dt>
                  <dd className="font-medium text-ink-800">{cafe?.slot_capacity ?? "-"} orders</dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-400">Hours</dt>
                  <dd className="font-medium text-ink-800">15-min windows</dd>
                </div>
              </dl>
              <p className="mt-3 text-xs leading-relaxed text-ink-400">
                {cafe?.opening_hours_summary}
              </p>
              <ButtonLink href="/merchant/settings" variant="outline" fullWidth className="mt-4">
                Edit cafe settings
              </ButtonLink>
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="font-semibold tracking-[-0.02em] text-ink-900">Quick actions</h2>
            <div className="mt-3 grid gap-2">
              <QuickLink href="/merchant/menu" icon={UtensilsCrossed} label="Update the menu" />
              <QuickLink href="/merchant/pickup-slots" icon={Clock3} label="Check pickup capacity" />
              <QuickLink href="/account" icon={UserRound} label="Account settings" />
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  note,
  tone = "neutral",
}: {
  icon: typeof Coffee;
  label: string;
  value: string;
  note: string;
  tone?: "neutral" | "brand" | "ready";
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-ink-500">
        <span
          className={
            tone === "brand"
              ? "text-brand-600"
              : tone === "ready"
                ? "text-ready-600"
                : "text-ink-400"
          }
        >
          <Icon className="size-4" aria-hidden />
        </span>
        {label}
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-ink-900">{value}</p>
      <p className="mt-1 text-xs text-ink-400">{note}</p>
    </Card>
  );
}

function QuickLink({
  href,
  icon: Icon,
  label,
}: {
  href: string;
  icon: typeof Coffee;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2.5 rounded-2xl border border-ink-100 px-3.5 py-3 text-sm font-medium text-ink-700 transition hover:border-ink-200 hover:bg-crema-50 hover:text-ink-900"
    >
      <Icon className="size-4 text-ink-400" aria-hidden />
      <span className="flex-1">{label}</span>
      <ArrowRight className="size-3.5 text-ink-300" aria-hidden />
    </Link>
  );
}
