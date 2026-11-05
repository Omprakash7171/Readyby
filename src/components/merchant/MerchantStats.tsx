"use client";

import { Banknote, CheckCheck, Clock3, Receipt } from "lucide-react";
import type { BoardSummary } from "@/lib/apiTypes";
import { cn, formatPrice } from "@/lib/format";

const cards = [
  { key: "orders_today", label: "ReadyBy orders today", icon: Receipt, tone: "ink" },
  { key: "pending", label: "In progress", icon: Clock3, tone: "brand" },
  { key: "ready", label: "Ready now", icon: CheckCheck, tone: "ready" },
  { key: "revenue_today", label: "Pickup sales today", icon: Banknote, tone: "dark" },
] as const;

const toneStyles: Record<string, { icon: string }> = {
  ink: { icon: "bg-ink-100 text-ink-600" },
  brand: { icon: "bg-brand-50 text-brand-600" },
  ready: { icon: "bg-ready-50 text-ready-600" },
  dark: { icon: "bg-ink-900 text-white" },
};

/**
 * Every figure comes from the API's board summary. Nothing is invented here, so
 * the numbers only reflect orders that really exist for this café.
 */
export function MerchantStats({
  summary,
  className,
}: {
  summary: BoardSummary;
  className?: string;
}) {
  return (
    <div className={className}>
      <ul className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          const styles = toneStyles[card.tone];
          const raw = summary[card.key];
          const value = card.key === "revenue_today" ? formatPrice(Number(raw)) : raw;

          return (
            <li
              key={card.key}
              className="rounded-3xl border border-ink-100 bg-white p-4 shadow-soft sm:p-5"
            >
              <div className="flex items-center gap-2.5">
                <span
                  aria-hidden
                  className={cn("grid size-8 shrink-0 place-items-center rounded-xl", styles.icon)}
                >
                  <Icon className="size-4" />
                </span>
                <p className="text-sm font-medium text-ink-500">{card.label}</p>
              </div>
              <p className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-ink-900 tabular-nums sm:text-3xl">
                {value}
              </p>
            </li>
          );
        })}
      </ul>
      <p className="mt-2.5 text-xs text-ink-400">
        Pickup sales count every order you have taken today, declined and
        cancelled orders excluded. {summary.dropped_today} dropped today.
      </p>
    </div>
  );
}