"use client";

import { useEffect, useState } from "react";
import { Clock3, RefreshCw } from "lucide-react";
import { ApiError, fetchMerchantPickupSlots } from "@/lib/api";
import type { MerchantPickupSlots } from "@/lib/apiTypes";
import { useRequireSession } from "@/context/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function MerchantPickupSlotsPage() {
  const session = useRequireSession(["MERCHANT", "ADMIN"]);
  const [data, setData] = useState<MerchantPickupSlots | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const body = await fetchMerchantPickupSlots(controller.signal);
        if (controller.signal.aborted) return;
        setData(body);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "We couldn't load pickup capacity. Check that the API is running.",
        );
      }
    })();
    return () => controller.abort();
  }, [session.user, reloadToken]);

  if (session.pending) return null;

  const full = (data?.slots ?? []).filter((slot) => slot.is_full).length;
  const open = (data?.slots ?? []).filter((slot) => !slot.is_full).length;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-[-0.035em] text-ink-900">
            Pickup slots
          </h1>
          <p className="mt-1.5 max-w-2xl text-pretty text-ink-500">
            Every arrival is booked into a 15-minute window. This is how much
            counter space is left in each one.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setReloadToken((n) => n + 1)}>
            <RefreshCw className="size-4" aria-hidden />
            Refresh
          </Button>
          <ButtonLink href="/merchant/settings" variant="dark">
            Change capacity
          </ButtonLink>
        </div>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="p-4">
          <p className="text-xs font-medium text-ink-500">Slot capacity</p>
          <p className="mt-2 text-2xl font-semibold text-ink-900">
            {data?.slot_capacity ?? "-"}
          </p>
          <p className="mt-1 text-xs text-ink-400">orders per window</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs font-medium text-ink-500">Open windows</p>
          <p className="mt-2 text-2xl font-semibold text-ready-700">{open}</p>
          <p className="mt-1 text-xs text-ink-400">in the next 24 hours</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs font-medium text-ink-500">Fully booked</p>
          <p className="mt-2 text-2xl font-semibold text-brand-700">{full}</p>
          <p className="mt-1 text-xs text-ink-400">windows at capacity</p>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="flex items-center gap-2 border-b border-ink-100 px-5 py-4">
          <Clock3 className="size-4 text-ink-400" aria-hidden />
          <h2 className="font-semibold tracking-[-0.02em] text-ink-900">
            Next 24 hours
          </h2>
        </div>
        {data === null ? (
          <div className="grid gap-2 p-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="h-24 animate-pulse rounded-2xl bg-ink-100" />
            ))}
          </div>
        ) : data.slots.length === 0 ? (
          <p className="px-5 py-12 text-center text-sm text-ink-500">
            No bookable slots right now. Check the cafe opening hours.
          </p>
        ) : (
          <ul className="grid gap-2 p-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.slots.map((slot) => {
              const used = slot.capacity - slot.remaining;
              const pct = Math.min(100, Math.round((used / slot.capacity) * 100));
              return (
                <li
                  key={slot.arrival_time}
                  className={
                    slot.is_full
                      ? "rounded-2xl border border-red-100 bg-red-50/60 p-3.5"
                      : "rounded-2xl border border-ink-100 bg-white p-3.5"
                  }
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-ink-900">{slot.time_label}</p>
                      <p className="mt-0.5 text-xs text-ink-400">{slot.day_label}</p>
                    </div>
                    {slot.is_full ? (
                      <Badge tone="danger">Full</Badge>
                    ) : (
                      <Badge tone="ready">{slot.remaining} left</Badge>
                    )}
                  </div>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-ink-100">
                    <div
                      className={slot.is_full ? "h-full rounded-full bg-red-400" : "h-full rounded-full bg-brand-500"}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-ink-500">
                    {used} of {slot.capacity} booked
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
