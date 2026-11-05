"use client";

import { ArrowRight, ShoppingBag, Trash2 } from "lucide-react";
import { cn, formatPrice } from "@/lib/format";
import type { BookingLine } from "@/context/BookingProvider";
import { useBooking } from "@/context/BookingProvider";
import { FoodArt } from "@/components/ui/FoodArt";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";

interface CartLinesProps {
  lines: BookingLine[];
  onIncrement: (menuItemId: number) => void;
  onDecrement: (menuItemId: number) => void;
  compact?: boolean;
  /** Shows a per-line total from server-sent prices, when available. */
  lineTotals?: Record<number, string>;
}

export function CartLines({
  lines,
  onIncrement,
  onDecrement,
  compact,
  lineTotals,
}: CartLinesProps) {
  if (lines.length === 0) return null;

  return (
    <ul className="divide-y divide-ink-100">
      {lines.map((line) => (
        <li
          key={line.menuItemId}
          className={cn(
            "flex items-center gap-3 py-3 first:pt-0 last:pb-0",
            compact && "py-2.5",
          )}
        >
          <FoodArt
            variant={line.art as never}
            className="size-11 shrink-0 rounded-xl ring-1 ring-ink-900/5"
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink-900">{line.name}</p>
            <p className="text-xs text-ink-500 tabular-nums">
              {formatPrice(line.price)} each
            </p>
          </div>

          <div className="flex items-center gap-1 rounded-full border border-ink-200 bg-crema-50 p-0.5">
            <button
              type="button"
              onClick={() => onDecrement(line.menuItemId)}
              aria-label={
                line.quantity === 1
                  ? `Remove ${line.name}`
                  : `Decrease quantity of ${line.name}`
              }
              className="grid size-7 place-items-center rounded-full text-ink-600 transition hover:bg-white active:scale-90"
            >
              <span className="text-base leading-none" aria-hidden>
                −
              </span>
            </button>
            <span
              className="w-5 text-center text-sm font-semibold text-ink-900 tabular-nums"
              aria-live="polite"
            >
              {line.quantity}
            </span>
            <button
              type="button"
              onClick={() => onIncrement(line.menuItemId)}
              aria-label={`Increase quantity of ${line.name}`}
              className="grid size-7 place-items-center rounded-full bg-white text-ink-800 shadow-sm transition hover:bg-ink-900 hover:text-white active:scale-90"
            >
              <span className="text-base leading-none" aria-hidden>
                +
              </span>
            </button>
          </div>

          <p className="w-16 text-right text-sm font-semibold text-ink-900 tabular-nums">
            {lineTotals?.[line.menuItemId]
              ? formatPrice(Number(lineTotals[line.menuItemId]))
              : formatPrice(line.price * line.quantity)}
          </p>
        </li>
      ))}
    </ul>
  );
}

/**
 * Checkout shows what the customer has in the basket. The figures are an
 * estimate until the order is placed: the server owns the real subtotal.
 */
export function OrderTotals({
  subtotal,
  total,
  estimated = true,
  className,
}: {
  subtotal: number | string;
  total?: number | string;
  estimated?: boolean;
  className?: string;
}) {
  const subtotalValue = typeof subtotal === "string" ? Number(subtotal) : subtotal;
  const totalValue = total === undefined ? subtotalValue : Number(total);

  return (
    <dl className={cn("space-y-2 text-sm", className)}>
      <div className="flex items-center justify-between">
        <dt className="text-ink-500">{estimated ? "Estimated total" : "Subtotal"}</dt>
        <dd className="font-medium text-ink-900 tabular-nums">
          {formatPrice(totalValue)}
        </dd>
      </div>
      <div className="flex items-center justify-between text-xs text-ink-400">
        <dt>{estimated ? "Confirmed at checkout" : "Pickup payment"}</dt>
        <dd>£0.00 service fee</dd>
      </div>
      {!estimated ? (
        <p className="pt-1 text-xs text-ink-400">
          Nothing to pay now — you pay at the counter when you collect.
        </p>
      ) : null}
    </dl>
  );
}

export function CartSheet({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const {
    cartLines,
    cartCount,
    cartEstimate,
    cafeName,
    incrementItem,
    decrementItem,
  } = useBooking();

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Your order"
      description={cafeName ? `From ${cafeName}` : undefined}
      placement="right"
      footer={
        cartLines.length ? (
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs text-ink-500">Estimated total</p>
              <p className="text-lg font-semibold text-ink-900 tabular-nums">
                {formatPrice(cartEstimate)}
              </p>
            </div>
            <ButtonLink href="/checkout" onClick={onClose}>
              Checkout
              <ArrowRight className="size-4" aria-hidden />
            </ButtonLink>
          </div>
        ) : null
      }
    >
      {cartCount === 0 ? (
        <EmptyState
          icon={<ShoppingBag className="size-6" />}
          title="Your order is empty"
          description="Add something from a nearby café and it will be ready when you arrive."
        />
      ) : (
        <div className="space-y-6">
          <CartLines
            lines={cartLines}
            onIncrement={incrementItem}
            onDecrement={decrementItem}
            compact
          />
          <OrderTotals
            subtotal={cartEstimate}
            className="rounded-2xl bg-crema-50 p-4"
          />
        </div>
      )}
    </Modal>
  );
}

export function CartFloatingBar({ onOpen }: { onOpen: () => void }) {
  const { cartCount, cartEstimate, cafeName } = useBooking();
  if (cartCount === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 px-4 pb-4 sm:px-6 sm:pb-6">
      <div className="pointer-events-auto mx-auto w-full max-w-md animate-fade-up">
        <button
          type="button"
          onClick={onOpen}
          className="flex w-full items-center gap-3 rounded-full bg-ink-900 py-2.5 pr-5 pl-2.5 text-left text-white shadow-pop transition hover:bg-ink-800 active:scale-[0.99]"
        >
          <span className="grid size-11 shrink-0 place-items-center rounded-full bg-brand-500 text-sm font-bold">
            {cartCount}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-semibold">
              {cafeName ?? "Your order"}
            </span>
            <span className="block text-xs text-white/60">
              View order · ready when you arrive
            </span>
          </span>
          <span className="text-sm font-semibold tabular-nums">
            {formatPrice(cartEstimate)}
          </span>
        </button>
      </div>
    </div>
  );
}

export function ClearCartButton() {
  const { clearCart } = useBooking();
  return (
    <Button variant="ghost" size="sm" onClick={clearCart}>
      <Trash2 className="size-3.5" aria-hidden />
      Clear
    </Button>
  );
}