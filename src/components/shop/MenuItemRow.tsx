"use client";

import { Check, Plus } from "lucide-react";
import type { ApiMenuItem } from "@/lib/apiTypes";
import { cn, formatPrice } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";
import { Photo } from "@/components/ui/Photo";

interface MenuItemRowProps {
  item: ApiMenuItem;
  quantity: number;
  onAdd: () => void;
  onIncrement: () => void;
  onDecrement: () => void;
}

export function MenuItemRow({
  item,
  quantity,
  onAdd,
  onIncrement,
  onDecrement,
}: MenuItemRowProps) {
  const inCart = quantity > 0;
  const unavailable = !item.is_available;

  return (
    <li
      className={cn(
        "group flex items-center gap-4 rounded-3xl border bg-white p-3 transition-all duration-300 sm:p-4",
        unavailable
          ? "border-ink-100 opacity-60"
          : inCart
            ? "border-brand-300 shadow-[0_8px_24px_-16px_rgba(193,69,31,0.7)]"
            : "border-ink-100 hover:-translate-y-0.5 hover:border-ink-200 hover:shadow-soft",
      )}
    >
      <Photo
        src={item.image_url}
        alt={item.name}
        art={item.art}
        className="size-16 shrink-0 rounded-2xl ring-1 ring-ink-900/5 sm:size-20"
      />

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-[0.98rem] font-semibold tracking-[-0.02em] text-ink-900">
            {item.name}
          </h3>
          {item.tag ? (
            <Badge tone="brand" className="py-0.5 text-[0.65rem]">
              {item.tag}
            </Badge>
          ) : null}
          {unavailable ? (
            <Badge tone="neutral" className="py-0.5 text-[0.65rem]">
              Sold out
            </Badge>
          ) : null}
        </div>
        <p className="mt-0.5 line-clamp-2 text-pretty text-sm leading-snug text-ink-500">
          {item.description}
        </p>
        <p className="mt-1.5 text-[0.98rem] font-semibold text-ink-900 tabular-nums">
          {formatPrice(Number(item.price))}
        </p>
      </div>

      <div className="shrink-0">
        {unavailable ? null : inCart ? (
          <div className="flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 p-1">
            <button
              type="button"
              onClick={onDecrement}
              aria-label={`Remove one ${item.name}`}
              className="grid size-8 place-items-center rounded-full text-brand-700 transition hover:bg-brand-100 active:scale-95"
            >
              {quantity === 1 ? (
                <Check className="size-4" aria-hidden />
              ) : (
                <span className="text-lg leading-none" aria-hidden>
                  −
                </span>
              )}
            </button>
            <span
              className="min-w-6 text-center text-sm font-semibold text-brand-800 tabular-nums"
              aria-live="polite"
            >
              {quantity}
            </span>
            <button
              type="button"
              onClick={onIncrement}
              aria-label={`Add one more ${item.name}`}
              className="grid size-8 place-items-center rounded-full bg-brand-500 text-white transition hover:bg-brand-600 active:scale-95"
            >
              <Plus className="size-4" aria-hidden />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={onAdd}
            aria-label={`Add ${item.name} to your order`}
            className="grid size-10 place-items-center rounded-full bg-ink-900 text-white transition-all duration-200 hover:bg-brand-500 hover:shadow-[0_8px_20px_-10px_rgba(225,85,46,0.9)] active:scale-90"
          >
            <Plus className="size-5" aria-hidden />
          </button>
        )}
      </div>
    </li>
  );
}