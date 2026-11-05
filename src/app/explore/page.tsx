"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, MapPin, Search, X } from "lucide-react";
import Link from "next/link";
import { ApiError, fetchCafes, fetchDestinations } from "@/lib/api";
import type { ApiCafe, ApiDestination } from "@/lib/apiTypes";
import { cn } from "@/lib/format";
import { useBooking } from "@/context/BookingProvider";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Field";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { DestinationIcon } from "@/components/ui/DestinationIcon";
import { ShopCard, ShopCardSkeleton } from "@/components/shop/ShopCard";
import { PickupTimeSelector } from "@/components/shop/PickupTimeSelector";

/** Stable empty list so an unfetched board never re-renders consumers. */
const NO_CAFES: ApiCafe[] = [];

export default function ExplorePage() {
  const { destinationKey, destinationName, selectDestination, arrivalAt, selectSoonestArrival } =
    useBooking();

  const [destinations, setDestinations] = useState<ApiDestination[]>([]);
  /**
   * The café list is tagged with the request it belongs to, so changing
   * destination shows a fresh fetch instead of the previous café's answers.
   */
  const [board, setBoard] = useState<{ key: string; cafes: ApiCafe[] } | null>(null);
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const result = await fetchDestinations(controller.signal);
        setDestinations(result.results);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError(
            err instanceof ApiError
              ? err.message
              : "We couldn't load destinations. Check that the API is running.",
          );
        }
      }
    })();
    return () => controller.abort();
  }, []);

  /**
   * The café list is entirely server-owned: the destination and arrival time go
   * out, and the API returns them ranked with distances, open states and a
   * ready-by plan for the exact arrival time.
   */
  useEffect(() => {
    if (!destinationKey) return;
    const key = `${destinationKey}|${arrivalAt ?? ""}`;
    const controller = new AbortController();
    void (async () => {
      setLoadingKey(key);
      try {
        const result = await fetchCafes(
          { destination: destinationKey, arrivalTime: arrivalAt ? new Date(arrivalAt).toISOString() : null },
          controller.signal,
        );
        setBoard({ key, cafes: result.results });
        setError(null);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError(
            err instanceof ApiError
              ? err.message
              : "We couldn't load cafés. Check that the API is running.",
          );
        }
      } finally {
        if (controller.signal.aborted) return;
        setLoadingKey((current) => (current === key ? null : current));
      }
    })();
    return () => controller.abort();
  }, [destinationKey, arrivalAt]);

  const cafes = board?.key === `${destinationKey}|${arrivalAt ?? ""}` ? board.cafes : NO_CAFES;
  const cafesLoading = loadingKey === `${destinationKey}|${arrivalAt ?? ""}`;

  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return destinations;
    return destinations.filter((item) =>
      `${item.name} ${item.kind} ${item.area}`.toLowerCase().includes(needle),
    );
  }, [destinations, query]);

  const hasQuery = query.trim().length > 0;
  const destination = destinations.find((item) => item.key === destinationKey) ?? null;
  const orderableCount = cafes.filter((cafe) => cafe.can_order).length;

  /** The nearest café that can serve the chosen arrival, for the timing note. */
  const previewCafe = cafes.find((cafe) => cafe.can_order) ?? null;

  function onPickDestination(item: ApiDestination) {
    selectDestination(item.key, item.name);
    // Arriving without a time chosen means the café list can't be ranked yet.
    if (arrivalAt === null) selectSoonestArrival();
    requestAnimationFrame(() => {
      document.getElementById("nearby-shops")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-10 sm:py-14">
      <header className="max-w-2xl">
        <p className="text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
          Step 1 · Destination
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-5xl">
          Where are you going?
        </h1>
        <p className="mt-3 text-pretty text-base text-ink-500 sm:text-lg">
          Tell us where you&rsquo;re heading and we&rsquo;ll show what&rsquo;s
          ready before you get there.
        </p>
      </header>

      <div className="mt-8 max-w-xl">
        <label htmlFor="destination-search" className="sr-only">
          Search a destination
        </label>
        <div className="relative">
          <Search
            className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-ink-400"
            aria-hidden
          />
          <Input
            id="destination-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search a destination…"
            autoComplete="off"
            className="h-14 rounded-2xl pr-12 pl-12 text-base shadow-soft"
          />
          {hasQuery ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Clear search"
              className="absolute top-1/2 right-3 grid size-8 -translate-y-1/2 place-items-center rounded-full text-ink-400 transition hover:bg-ink-100 hover:text-ink-700"
            >
              <X className="size-4" aria-hidden />
            </button>
          ) : null}
        </div>
      </div>

      {error ? (
        <p
          role="alert"
          className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </p>
      ) : null}

      {destinations.length === 0 && !error ? (
        <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((index) => (
            <li key={index} className="h-24 animate-pulse rounded-3xl bg-ink-100" />
          ))}
        </ul>
      ) : matches.length === 0 ? (
        <EmptyState
          className="mt-6"
          icon={<MapPin className="size-6" />}
          title="No destinations match that"
          description="Try a different word, or clear the search to see every destination."
          actionLabel="Show all destinations"
          actionHref="/explore"
        />
      ) : (
        <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {matches.map((item) => {
            const selected = item.key === destinationKey;
            return (
              <li key={item.key}>
                <button
                  type="button"
                  onClick={() => onPickDestination(item)}
                  aria-pressed={selected}
                  className={cn(
                    "group flex h-full w-full items-start gap-3.5 rounded-3xl border p-4 text-left transition-all duration-300",
                    selected
                      ? "border-ink-900 bg-ink-900 text-white shadow-lift"
                      : "border-ink-100 bg-white shadow-soft hover:-translate-y-1 hover:border-ink-200 hover:shadow-lift",
                  )}
                >
                  <span
                    className={cn(
                      "grid size-11 shrink-0 place-items-center rounded-2xl transition-colors",
                      selected
                        ? "bg-white/12 text-white"
                        : "bg-crema-100 text-brand-600 group-hover:bg-brand-50",
                    )}
                  >
                    <DestinationIcon icon={item.icon} className="size-5" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span
                      className={cn(
                        "block truncate text-[0.98rem] font-semibold tracking-[-0.02em]",
                        selected ? "text-white" : "text-ink-900",
                      )}
                    >
                      {item.name}
                    </span>
                    <span
                      className={cn(
                        "mt-0.5 block text-sm",
                        selected ? "text-white/60" : "text-ink-500",
                      )}
                    >
                      {item.kind} · {item.area}
                    </span>
                    <span
                      className={cn(
                        "mt-1.5 block text-xs",
                        selected ? "text-white/50" : "text-ink-400",
                      )}
                    >
                      {item.note}
                    </span>
                  </span>
                  {selected ? (
                    <ArrowRight className="size-4 shrink-0 text-white/70" aria-hidden />
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <section
        id="nearby-shops"
        aria-labelledby="nearby-shops-heading"
        className="scroll-mt-24 pt-14 sm:pt-20"
      >
        {destinationKey ? (
          <>
            <div>
              <p className="text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
                Step 2 · Arrival time
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-ink-900 sm:text-3xl">
                When will you arrive?
              </h2>
              <p className="mt-2 text-pretty text-sm text-ink-500">
                Every café below shows what it can have ready for that time.
              </p>
            </div>

            <Card className="mt-6 p-5 sm:p-6">
              <PickupTimeSelector cafe={previewCafe} />
            </Card>

            <div className="mt-14 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between sm:pt-4">
              <div>
                <p className="text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
                  Step 3 · Nearby shops
                </p>
                <h2
                  id="nearby-shops-heading"
                  className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-ink-900 sm:text-3xl"
                >
                  Ready for your arrival
                </h2>
                <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-500">
                  {destination ? <DestinationIcon icon={destination.icon} className="size-4" /> : null}
                  <span>
                    Walking distance from{" "}
                    <span className="font-medium text-ink-800">{destinationName}</span>
                  </span>
                </p>
              </div>
              {!cafesLoading ? (
                <Badge tone="ready" className="self-start sm:self-auto">
                  {orderableCount} open for your time
                </Badge>
              ) : null}
            </div>

            {cafesLoading ? (
              <ul className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {[0, 1, 2].map((index) => (
                  <ShopCardSkeleton key={index} />
                ))}
              </ul>
            ) : cafes.length === 0 ? (
              <EmptyState
                className="mt-6"
                icon={<MapPin className="size-6" />}
                title="No cafés serve that arrival time"
                description="Try a later time, or choose another destination."
              />
            ) : (
              <ul className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {cafes.map((cafe, index) => (
                  <ShopCard
                    key={cafe.slug}
                    cafe={cafe}
                    className="h-full animate-fade-up"
                    style={{ animationDelay: `${index * 60}ms` }}
                  />
                ))}
              </ul>
            )}

            <Card className="mt-6 flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-pretty text-sm text-ink-500">
                ReadyBy is pickup only. Nothing is delivered — you come to the
                counter.
              </p>
              <Link
                href="/merchant"
                className="inline-flex shrink-0 items-center gap-1.5 text-sm font-semibold text-brand-600 transition hover:gap-2.5"
              >
                Café sign-in
                <ArrowRight className="size-4" aria-hidden />
              </Link>
            </Card>
          </>
        ) : (
          <Card className="flex flex-col items-center px-6 py-14 text-center">
            <span
              aria-hidden
              className="grid size-14 place-items-center rounded-2xl bg-crema-100 text-ink-400"
            >
              <MapPin className="size-6" />
            </span>
            <h2 className="mt-5 text-lg font-semibold tracking-[-0.02em] text-ink-900">
              Choose a destination to see nearby shops
            </h2>
            <p className="mt-2 max-w-sm text-pretty text-sm leading-relaxed text-ink-500">
              We&rsquo;ll list the cafés within walking distance and how long
              each one takes to reach from where you&rsquo;re going.
            </p>
          </Card>
        )}
      </section>
    </div>
  );
}