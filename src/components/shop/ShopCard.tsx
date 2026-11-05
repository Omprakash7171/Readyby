import Link from "next/link";
import type { CSSProperties } from "react";
import { ArrowRight, Timer } from "lucide-react";
import type { ApiCafe } from "@/lib/apiTypes";
import { cn } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Photo } from "@/components/ui/Photo";
import { MetaRow, OpenBadge, Stars } from "@/components/ui/Meta";
import { ReadyByBadge } from "@/components/shop/ReadyByBadge";

interface ShopCardProps {
  cafe: ApiCafe;
  className?: string;
  style?: CSSProperties;
}

/**
 * A café exactly as the API ranked it for the selected destination and arrival
 * time: distance, walk, open state and the ready-by plan are all server-owned.
 */
export function ShopCard({ cafe, className, style }: ShopCardProps) {
  const orderable = cafe.can_order;

  return (
    <Card
      as="li"
      style={style}
      interactive={orderable}
      className={cn("group relative overflow-hidden", className)}
    >
      {!orderable ? (
        <div
          aria-disabled
          className="flex h-full cursor-not-allowed flex-col p-5 opacity-70"
        >
          <ShopCardBody cafe={cafe} />
          <ShopCardFooter cafe={cafe} />
        </div>
      ) : (
        <Link
          href={`/shop/${cafe.slug}`}
          aria-label={`View menu at ${cafe.name}`}
          className="flex h-full flex-col p-5"
        >
          <ShopCardBody cafe={cafe} />
          <ShopCardFooter cafe={cafe} />
        </Link>
      )}
    </Card>
  );
}

function ShopCardBody({ cafe }: { cafe: ApiCafe }) {
  return (
    <div className="flex items-start gap-4">
      <Photo
        src={cafe.image_url}
        alt={`${cafe.name} interior`}
        art="hot-cup"
        className="size-14 shrink-0 rounded-2xl ring-1 ring-ink-900/5"
      />
      <div className="min-w-0 flex-1">
        <p className="text-[0.7rem] font-semibold tracking-[0.14em] text-brand-600 uppercase">
          {cafe.category}
        </p>
        <div className="mt-1 flex items-start justify-between gap-2">
          <h3 className="truncate text-[1.05rem] font-semibold tracking-[-0.02em] text-ink-900">
            {cafe.name}
          </h3>
          <Stars rating={Number(cafe.rating)} showValue={false} />
        </div>
        <p className="mt-0.5 text-sm text-ink-500">{cafe.tagline}</p>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-700">
            <span className="text-amber-400" aria-hidden>
              ★
            </span>
            {Number(cafe.rating).toFixed(1)}
          </span>
          <MetaRow distanceMetres={cafe.distance_metres} walkMinutes={cafe.walk_minutes} />
          <span className="inline-flex items-center gap-1.5 text-sm text-ink-600">
            <Timer className="size-3.5 text-ink-400" aria-hidden />
            {cafe.prep_time_minutes} min prep
          </span>
        </div>
      </div>
    </div>
  );
}

function ShopCardFooter({ cafe }: { cafe: ApiCafe }) {
  return (
    <div className="mt-auto flex flex-col gap-3 border-t border-ink-100 pt-4">
      {cafe.estimated_ready_time_label ? (
        <ReadyByBadge
          readyLabel={cafe.estimated_ready_time_label}
          startLabel={cafe.start_preparing_time_label}
          size="sm"
        />
      ) : null}
      <div className="flex items-center justify-between gap-3">
        <OpenBadge
          state={cafe.open_state}
          hours={cafe.can_order ? (cafe.open_state_label ?? undefined) : undefined}
        />
        <span
          className={cn(
            "inline-flex items-center gap-1.5 text-sm font-semibold transition-all duration-200",
            cafe.can_order ? "text-brand-600 group-hover:gap-2.5" : "text-ink-400",
          )}
        >
          {cafe.can_order ? "View menu" : "Unavailable"}
          {cafe.can_order ? (
            <ArrowRight
              className="size-4 transition-transform duration-200 group-hover:translate-x-0.5"
              aria-hidden
            />
          ) : null}
        </span>
      </div>
      {!cafe.can_order && cafe.unavailable_reason ? (
        <p className="text-xs text-ink-400">{cafe.unavailable_reason}</p>
      ) : null}
    </div>
  );
}

export function ShopCardSkeleton() {
  return (
    <Card as="li" className="animate-pulse p-5">
      <div className="flex items-start gap-4">
        <div className="size-14 shrink-0 rounded-2xl bg-ink-100" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-2/3 rounded-full bg-ink-100" />
          <div className="h-3 w-1/2 rounded-full bg-ink-100" />
          <div className="h-3 w-3/4 rounded-full bg-ink-100" />
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between border-t border-ink-100 pt-4">
        <div className="h-6 w-28 rounded-full bg-ink-100" />
        <div className="h-4 w-20 rounded-full bg-ink-100" />
      </div>
    </Card>
  );
}