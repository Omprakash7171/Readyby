"use client";

import { use, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Clock, Info, MapPin, ShoppingBag } from "lucide-react";
import { ApiError, fetchCafe, fetchMenu } from "@/lib/api";
import type { ApiCafe, ApiMenuItem } from "@/lib/apiTypes";
import { cn, formatPrice } from "@/lib/format";
import { useBooking } from "@/context/BookingProvider";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { MetaRow, OpenBadge, Stars } from "@/components/ui/Meta";
import { ReadyByBadge } from "@/components/shop/ReadyByBadge";
import { Photo } from "@/components/ui/Photo";
import { MenuItemRow } from "@/components/shop/MenuItemRow";
import { CartSheet, CartFloatingBar } from "@/components/shop/Cart";

export default function ShopPage({ params }: { params: Promise<{ shopId: string }> }) {
  const { shopId } = use(params);

  const { destinationKey, arrivalAt, selectCafe, addItem, incrementItem, decrementItem, itemQuantity } =
    useBooking();

  const [cartOpen, setCartOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>("");
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});

  /**
   * Everything the page shows is tagged with the request that produced it, so
   * moving to another café or another arrival time shows a loading state rather
   * than the previous answer. No effect has to reset state to get there.
   */
  const [load, setLoad] = useState<{
    key: string;
    cafe: ApiCafe | null;
    items: ApiMenuItem[] | null;
    error: string | null;
    notFound: boolean;
  } | null>(null);

  const requestKey = `${shopId}|${destinationKey ?? ""}|${arrivalAt ?? ""}`;
  const current = load?.key === requestKey ? load : null;
  const cafe = current?.cafe ?? null;
  const items = current?.items ?? null;
  const error = current?.error ?? null;
  const notFound = current?.notFound ?? false;

  useEffect(() => {
    const controller = new AbortController();
    const key = `${shopId}|${destinationKey ?? ""}|${arrivalAt ?? ""}`;

    void (async () => {
      try {
        const detail = await fetchCafe(
          shopId,
          {
            destination: destinationKey,
            arrivalTime: arrivalAt ? new Date(arrivalAt).toISOString() : null,
          },
          controller.signal,
        );
        selectCafe(detail.slug, detail.name);
        setLoad({ key, cafe: detail, items: null, error: null, notFound: false });

        const menu = await fetchMenu(shopId, controller.signal);
        setLoad({ key, cafe: detail, items: menu.items, error: null, notFound: false });
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        if (err instanceof ApiError && err.isNotFound) {
          setLoad({ key, cafe: null, items: null, error: null, notFound: true });
          return;
        }
        setLoad({
          key,
          cafe: null,
          items: null,
          error:
            err instanceof ApiError
              ? err.message
              : "We couldn't load this café. Check that the API is running.",
          notFound: false,
        });
      }
    })();

    return () => controller.abort();
  }, [shopId, destinationKey, arrivalAt, selectCafe]);

  const groups = useMemo(() => {
    if (!items) return [];
    const byCategory = new Map<string, ApiMenuItem[]>();
    for (const item of items) {
      const bucket = byCategory.get(item.category);
      if (bucket) bucket.push(item);
      else byCategory.set(item.category, [item]);
    }
    return [...byCategory.entries()].map(([category, groupItems]) => ({
      category,
      items: groupItems,
    }));
  }, [items]);

  /** Falls back to the first category until the customer picks one. */
  const visibleCategory = groups.some((group) => group.category === activeCategory)
    ? activeCategory
    : (groups[0]?.category ?? "");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActiveCategory(visible[0].target.id);
      },
      { rootMargin: "-140px 0px -65% 0px", threshold: 0 },
    );

    for (const group of groups) {
      const node = sectionRefs.current[group.category];
      if (node) observer.observe(node);
    }
    return () => observer.disconnect();
  }, [groups]);

  if (notFound) {
    return (
      <div className="mx-auto w-full max-w-2xl px-5 py-24 text-center">
        <h1 className="text-2xl font-semibold tracking-[-0.03em] text-ink-900">
          We couldn&rsquo;t find that café
        </h1>
        <p className="mt-3 text-pretty text-ink-500">
          It may have stopped taking ReadyBy orders.
        </p>
        <Link
          href="/explore"
          className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:gap-2.5"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to nearby cafés
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto w-full max-w-2xl px-5 py-24 text-center">
        <h1 className="text-2xl font-semibold tracking-[-0.03em] text-ink-900">
          We couldn&rsquo;t load this café
        </h1>
        <p role="alert" className="mt-3 text-pretty text-ink-500">
          {error}
        </p>
        <Link
          href="/explore"
          className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:gap-2.5"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to nearby cafés
        </Link>
      </div>
    );
  }

  if (!cafe || !items) {
    return (
      <div className="mx-auto w-full max-w-6xl animate-pulse space-y-6 px-5 py-12">
        <div className="h-5 w-40 rounded-full bg-ink-100" />
        <div className="h-64 rounded-3xl bg-ink-100" />
        <div className="h-96 rounded-3xl bg-ink-100" />
      </div>
    );
  }

  const categoryId = (category: string) => category.replace(/\s+/g, "-").toLowerCase();

  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-8 sm:py-12">
      <Link
        href="/explore"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 transition hover:gap-2.5 hover:text-ink-900"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to nearby cafés
      </Link>

      <Card className="mt-5 overflow-hidden">
        <div className="grid gap-6 p-5 sm:p-7 lg:grid-cols-[1fr_auto] lg:items-start">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2.5">
              <Badge tone="neutral">{cafe.category}</Badge>
              <OpenBadge
                state={cafe.open_state}
                hours={cafe.open_state_label ?? undefined}
              />
              <Badge tone="info">
                <MapPin className="size-3.5" aria-hidden />
                Pickup only
              </Badge>
            </div>

            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-4xl">
              {cafe.name}
            </h1>
            <p className="mt-1 text-base text-ink-500">{cafe.tagline}</p>

            <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-3">
              <Stars rating={Number(cafe.rating)} />
              <MetaRow
                distanceMetres={cafe.distance_metres}
                walkMinutes={cafe.walk_minutes}
              />
              <span className="inline-flex items-center gap-1.5 text-sm text-ink-500">
                <Clock className="size-3.5 text-ink-400" aria-hidden />
                Ready in {cafe.prep_time_minutes} min
              </span>
            </div>

            <p className="mt-5 max-w-2xl text-pretty text-sm leading-relaxed text-ink-500">
              {cafe.description}
            </p>
          </div>

          <Photo
            src={cafe.image_url}
            alt={`${cafe.name} interior`}
            art="hot-cup"
            banner
            className="h-32 w-full rounded-2xl ring-1 ring-ink-900/5 lg:h-28 lg:w-56"
          />
        </div>

        {cafe.can_order && cafe.estimated_ready_time_label ? (
          <div className="flex flex-wrap items-center gap-3 border-t border-ink-100 bg-crema-50 px-5 py-3.5 sm:px-7">
            <p className="text-sm text-ink-600">
              Ready when you arrive
              {cafe.walk_minutes !== null ? (
                <>
                  {" "}
                  · {cafe.walk_minutes} min walk
                </>
              ) : null}
            </p>
            <ReadyByBadge
              readyLabel={cafe.estimated_ready_time_label}
              startLabel={cafe.start_preparing_time_label}
              size="sm"
              className="sm:ml-auto"
            />
          </div>
        ) : (
          <div className="flex items-center gap-3 border-t border-ink-100 bg-crema-50 px-5 py-3.5 sm:px-7">
            <Info className="size-4 shrink-0 text-ink-400" aria-hidden />
            <p className="text-sm text-ink-500">
              {cafe.unavailable_reason ??
                "Pick a destination and arrival time on the nearby page to check availability."}
            </p>
          </div>
        )}
      </Card>

      <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_20rem] lg:items-start">
        <div className="min-w-0">
          <nav
            aria-label="Menu categories"
            className="no-scrollbar sticky top-16 z-30 mb-6 flex gap-2 overflow-x-auto rounded-full bg-crema-50/90 p-1.5 backdrop-blur-lg sm:px-3"
          >
            {groups.map((group) => (
              <a
                key={group.category}
                href={`#${categoryId(group.category)}`}
                onClick={() => setActiveCategory(group.category)}
                className={cn(
                  "shrink-0 rounded-full px-3.5 py-2 text-sm font-medium transition-colors",
                  visibleCategory === group.category
                    ? "bg-ink-900 text-white"
                    : "bg-white text-ink-600 ring-1 ring-ink-100 hover:text-ink-900",
                )}
              >
                {group.category}
              </a>
            ))}
          </nav>

          <div className="space-y-10">
            {groups.map((group) => (
              <section
                key={group.category}
                id={categoryId(group.category)}
                ref={(node) => {
                  sectionRefs.current[group.category] = node;
                }}
                aria-labelledby={`${categoryId(group.category)}-heading`}
                className="scroll-mt-32"
              >
                <h2
                  id={`${categoryId(group.category)}-heading`}
                  className="text-xl font-semibold tracking-[-0.025em] text-ink-900"
                >
                  {group.category}
                </h2>
                <ul className="mt-4 space-y-3">
                  {group.items.map((item) => (
                    <MenuItemRow
                      key={item.id}
                      item={item}
                      quantity={itemQuantity(item.id)}
                      onAdd={() => addItem(item)}
                      onIncrement={() => incrementItem(item.id)}
                      onDecrement={() => decrementItem(item.id)}
                    />
                  ))}
                </ul>
              </section>
            ))}
          </div>

          <Card className="mt-10 flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="flex items-start gap-2 text-sm text-ink-500">
              <MapPin className="mt-0.5 size-4 shrink-0 text-ink-400" aria-hidden />
              ReadyBy orders are prepared in the order they are placed. No
              delivery, no courier.
            </p>
          </Card>
        </div>

        <aside className="hidden lg:sticky lg:top-32 lg:block">
          <OrderSummaryCard onCheckout={() => setCartOpen(true)} />
        </aside>
      </div>

      <CartFloatingBar onOpen={() => setCartOpen(true)} />
      <CartSheet open={cartOpen} onClose={() => setCartOpen(false)} />
    </div>
  );
}

function OrderSummaryCard({ onCheckout }: { onCheckout: () => void }) {
  const { cartCount, cartEstimate, cartLines, cafeName, cafeSlug } = useBooking();
  const forThisCafe = cafeSlug !== null;

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-ink-100 bg-crema-50 px-5 py-4">
        <h2 className="text-sm font-semibold tracking-[-0.01em] text-ink-900">Your order</h2>
      </div>
      <div className="px-5 py-5">
        {cartCount === 0 || !forThisCafe ? (
          <>
            <p className="text-pretty text-sm leading-relaxed text-ink-500">
              Add an item and choose a pickup time that matches your journey.
            </p>
            <button
              type="button"
              disabled={cartCount === 0}
              onClick={onCheckout}
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-brand-500 px-5 py-3 text-[0.95rem] font-medium text-white transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98]"
            >
              <ShoppingBag className="size-4" aria-hidden />
              View order
            </button>
          </>
        ) : (
          <>
            <p className="text-sm text-ink-600">
              {cartCount} {cartCount === 1 ? "item" : "items"} · {cafeName}
            </p>
            <p className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-ink-900 tabular-nums">
              {formatPrice(cartEstimate)}
            </p>
            <p className="mt-1 text-xs text-ink-400">Confirmed by the café at checkout</p>
            <button
              type="button"
              onClick={onCheckout}
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-brand-500 px-5 py-3 text-[0.95rem] font-medium text-white transition hover:bg-brand-600 active:scale-[0.98]"
            >
              Checkout
            </button>
          </>
        )}
      </div>
      {cartCount > 0 && forThisCafe && cartLines.length ? (
        <ul className="border-t border-ink-100 px-5 py-4">
          {cartLines.map((line) => (
            <li
              key={line.menuItemId}
              className="flex items-center justify-between gap-3 py-1 text-sm text-ink-600"
            >
              <span className="truncate">
                {line.quantity} × {line.name}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}