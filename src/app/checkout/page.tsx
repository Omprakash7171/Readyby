"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, MapPin, ShieldCheck } from "lucide-react";
import { ApiError, createOrder, fetchCafe, fetchPickupQuote, newIdempotencyKey } from "@/lib/api";
import type { ApiCafe, PickupQuote } from "@/lib/apiTypes";
import { cn, formatPrice } from "@/lib/format";
import { useBooking } from "@/context/BookingProvider";
import { useRequireSession } from "@/context/SessionProvider";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { OpenBadge, Stars } from "@/components/ui/Meta";
import { CartLines, OrderTotals } from "@/components/shop/Cart";
import { PickupTimeSelector } from "@/components/shop/PickupTimeSelector";
import { ReadyByBadge } from "@/components/shop/ReadyByBadge";

export default function CheckoutPage() {
  const router = useRouter();
  const session = useRequireSession();
  const {
    cartLines,
    cartEstimate,
    cafeSlug,
    cafeName,
    destinationKey,
    destinationName,
    arrivalIso,
    hasArrival,
    incrementItem,
    decrementItem,
    clearCart,
  } = useBooking();

  const [cafe, setCafe] = useState<ApiCafe | null>(null);
  const [quoteState, setQuoteState] = useState<{
    key: string;
    quote: PickupQuote | null;
    error: string | null;
  } | null>(null);
  const [quoteRevision, setQuoteRevision] = useState(0);
  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  /**
   * One idempotency key per checkout attempt. Generated once here so a double
   * click, a retry after a timeout, or a flaky connection resolves to the same
   * order instead of two.
   */
  const idempotencyKey = useRef<string>(newIdempotencyKey());

  useEffect(() => {
    if (!cafeSlug) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const detail = await fetchCafe(
          cafeSlug,
          {
            destination: destinationKey,
            arrivalTime: arrivalIso,
          },
          controller.signal,
        );
        setCafe(detail);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError(
            err instanceof ApiError
              ? err.message
              : "We couldn't check this café's availability.",
          );
        }
      }
    })();
    return () => controller.abort();
  }, [cafeSlug, destinationKey, arrivalIso]);

  const items = useMemo(
    () =>
      cartLines.map((line) => ({
        menu_item: line.menuItemId,
        quantity: line.quantity,
      })),
    [cartLines],
  );

  const quoteKey = useMemo(
    () =>
      `${cafeSlug ?? ""}|${arrivalIso ?? ""}|${quoteRevision}|${items
        .map((item) => `${item.menu_item}x${item.quantity}`)
        .join(",")}`,
    [cafeSlug, arrivalIso, quoteRevision, items],
  );

  useEffect(() => {
    if (!cafeSlug || !arrivalIso || items.length === 0) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const body = await fetchPickupQuote(
          cafeSlug,
          { items, arrivalTime: arrivalIso },
          controller.signal,
        );
        setQuoteState({ key: quoteKey, quote: body, error: null });
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setQuoteState({
          key: quoteKey,
          quote: null,
          error:
            err instanceof ApiError
              ? err.message
              : "We couldn't check live pickup slots.",
        });
      }
    })();
    return () => controller.abort();
  }, [cafeSlug, arrivalIso, items, quoteKey]);

  const currentQuote = quoteState?.key === quoteKey ? quoteState.quote : null;
  const quoteError = quoteState?.key === quoteKey ? quoteState.error : null;
  const quoteLoading = Boolean(
    cafeSlug && arrivalIso && items.length > 0 && quoteState?.key !== quoteKey,
  );
  const slotProblem = currentQuote?.requested_slot?.problem ?? null;
  const quoteBlockReason = !currentQuote
    ? null
    : !currentQuote.is_accepting_orders
      ? "This café isn't taking orders right now."
      : currentQuote.unavailable_items.length > 0
        ? `${currentQuote.unavailable_items.join(", ")} ${
            currentQuote.unavailable_items.length === 1 ? "is" : "are"
          } sold out.`
        : currentQuote.missing_item_ids.length > 0
          ? "An item on your order is no longer on this café's menu."
          : slotProblem;

  const handlePlaceOrder = useCallback(async () => {
    if (placing || !cafeSlug || !arrivalIso || items.length === 0) return;
    setPlacing(true);
    setError(null);
    try {
      const order = await createOrder(
        {
          cafe: cafeSlug,
          destination: destinationKey,
          arrivalTime: arrivalIso,
          items,
          notes,
        },
        idempotencyKey.current,
      );
      clearCart();
      router.replace(`/confirmation/${order.public_id}`);
    } catch (err) {
      setPlacing(false);
      if (err instanceof ApiError && err.isUnauthenticated) {
        router.push(
          `/login?next=${encodeURIComponent("/checkout")}`,
        );
        return;
      }
      if (err instanceof ApiError && err.code === "slot_full") {
        setQuoteRevision((value) => value + 1);
      }
      setError(
        err instanceof ApiError
          ? err.message
          : "We couldn't place that order. Please try again.",
      );
    }
  }, [placing, cafeSlug, arrivalIso, destinationKey, items, notes, clearCart, router]);

  if (session.pending) return null;

  if (cartLines.length === 0 || !cafeSlug) {
    return (
      <div className="mx-auto w-full max-w-3xl px-5 py-14 sm:py-20">
        <EmptyState
          icon={<MapPin className="size-6" />}
          title="Nothing in your order yet"
          description="Pick a destination, choose a nearby café and add what you want. It'll be ready when you arrive."
          actionLabel="Find nearby cafés"
          actionHref="/explore"
        />
      </div>
    );
  }

  const unavailableReason =
    quoteBlockReason ?? (cafe !== null && !cafe.can_order ? cafe.unavailable_reason : null);
  const unavailable = unavailableReason !== null;
  const blocked = !hasArrival || unavailable;

  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-8 pb-32 sm:py-12 lg:pb-16">
      <Link
        href={`/shop/${cafeSlug}`}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 transition hover:gap-2.5 hover:text-ink-900"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to {cafeName}
      </Link>

      <header className="mt-5">
        <p className="text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
          Checkout
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-5xl">
          Your order
        </h1>
        <p className="mt-3 text-pretty text-base text-ink-500">
          {cafeName} prepares for your arrival time, not a generic pickup window.
        </p>
      </header>

      <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_22rem] lg:items-start">
        <div className="space-y-6">
          <Card className="p-5 sm:p-6">
            <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">Items</h2>
            <div className="mt-4">
              <CartLines
                lines={cartLines}
                onIncrement={incrementItem}
                onDecrement={decrementItem}
              />
            </div>
          </Card>

          <Card className="p-5 sm:p-6">
            <PickupTimeSelector
              cafe={cafe}
              slots={currentQuote?.slots}
              loading={quoteLoading}
              notice={
                slotProblem ??
                (quoteError
                  ? `Live slots couldn't be checked. ${quoteError}`
                  : null)
              }
            />
          </Card>

          <Card className="p-5 sm:p-6">
            <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
              Where you&rsquo;re heading
            </h2>
            {destinationName ? (
              <p className="mt-3 text-sm text-ink-600">
                Ordering for{" "}
                <span className="font-semibold text-ink-900">{destinationName}</span>
                {cafe?.walk_minutes !== null && cafe?.walk_minutes !== undefined ? (
                  <>
                    {" "}
                    · {cafe.walk_minutes} min walk
                  </>
                ) : null}
              </p>
            ) : (
              <p className="mt-3 text-sm text-ink-500">
                No destination set yet.{" "}
                <Link href="/explore" className="font-semibold text-brand-600 hover:underline">
                  Choose one
                </Link>{" "}
                so we can time your order correctly.
              </p>
            )}
          </Card>

          <Card className="p-5 sm:p-6">
            <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
              Anything else?
            </h2>
            <p className="mt-2 text-sm text-ink-500">
              Optional note for the café — up to 280 characters.
            </p>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              maxLength={280}
              rows={3}
              aria-label="Note for the café"
              className="mt-3 w-full rounded-2xl border border-ink-200 bg-white px-4 py-3 text-ink-900 placeholder:text-ink-300 focus:border-brand-400 focus:ring-4 focus:ring-brand-500/10 focus:outline-none"
              placeholder="e.g. Extra hot, oat milk if you have it"
            />
            <p className="mt-1 text-right text-xs text-ink-400 tabular-nums">
              {notes.length}/280
            </p>
          </Card>

          {cafe?.estimated_ready_time_label ? (
            <Card className="p-5 sm:p-6">
              <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
                When you arrive
              </h2>
              <p className="mt-3 text-pretty text-sm leading-relaxed text-ink-600">
                {cafe.name} starts preparing around{" "}
                <span className="font-semibold text-ink-900">
                  {cafe.start_preparing_time_label}
                </span>{" "}
                so your order is finished by{" "}
                <span className="font-semibold text-ink-900">
                  {cafe.estimated_ready_time_label}
                </span>
                . Show your order number at the counter &mdash; no queue.
              </p>
              <ul className="mt-4 space-y-2.5">
                {[
                  "Walk in at your arrival time and give the counter your order number.",
                  "Nothing is delivered — the café is waiting for you, not you for it.",
                  "If you run a little early or late, it will still be waiting at the counter.",
                ].map((line) => (
                  <li key={line} className="flex items-start gap-2.5 text-sm text-ink-600">
                    <ShieldCheck className="mt-0.5 size-4 shrink-0 text-ready-500" aria-hidden />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}
        </div>

        <aside className="lg:sticky lg:top-24">
          <Card className="overflow-hidden">
            <div className="border-b border-ink-100 bg-crema-50 px-5 py-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-semibold text-ink-900">{cafeName}</h2>
                  {cafe ? (
                    <div className="mt-1">
                      <Stars rating={Number(cafe.rating)} />
                    </div>
                  ) : null}
                </div>
                {cafe ? (
                  <OpenBadge state={cafe.open_state} className="shrink-0" />
                ) : null}
              </div>
            </div>

            <div className="px-5 py-5">
              {cafe?.estimated_ready_time_label ? (
                <ReadyByBadge
                  readyLabel={cafe.estimated_ready_time_label}
                  startLabel={cafe.start_preparing_time_label}
                  className="mb-4 w-full justify-center"
                />
              ) : null}

              <OrderTotals subtotal={cartEstimate} />

              {error ? (
                <p
                  role="alert"
                  className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                >
                  {error}
                </p>
              ) : null}

              {unavailable && unavailableReason ? (
                <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  {unavailableReason}
                </p>
              ) : null}

              <Button
                size="lg"
                fullWidth
                onClick={() => void handlePlaceOrder()}
                disabled={placing || blocked || unavailable}
                className="mt-5"
              >
                {placing ? "Placing order…" : "Place order"}
                <ArrowRight className="size-4.5" aria-hidden />
              </Button>

              {blocked ? (
                <p className="mt-2 text-center text-xs text-ink-400">
                  {!hasArrival ? "Choose an arrival time first" : unavailableReason}
                </p>
              ) : (
                <p className="mt-3 text-center text-xs text-ink-400">
                  Nothing to pay now — you pay at the counter
                </p>
              )}
            </div>
          </Card>
        </aside>
      </div>

      <div
        className={cn(
          "fixed inset-x-0 bottom-0 z-30 border-t border-ink-100 bg-white/95 px-5 py-3 backdrop-blur-lg transition lg:hidden",
          "pb-[max(0.75rem,env(safe-area-inset-bottom))]",
        )}
      >
        <div className="flex items-center gap-3">
          <div className="min-w-0">
            <p className="text-xs text-ink-500">Estimated total</p>
            <p className="text-lg font-semibold text-ink-900 tabular-nums">
              {formatPrice(cartEstimate)}
            </p>
          </div>
          <Button
            onClick={() => void handlePlaceOrder()}
            disabled={placing || blocked || unavailable}
            className="ml-auto flex-1"
            size="lg"
          >
            {placing ? "Placing order…" : "Place order"}
          </Button>
        </div>
      </div>
    </div>
  );
}