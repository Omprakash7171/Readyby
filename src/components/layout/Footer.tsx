"use client";

import Link from "next/link";
import { RotateCcw } from "lucide-react";
import { useBooking } from "@/context/BookingProvider";
import { Logo } from "@/components/ui/Logo";
import { Button } from "@/components/ui/Button";

export function Footer() {
  const { reset } = useBooking();

  return (
    <footer className="mt-auto border-t border-ink-100 bg-white">
      <div className="mx-auto w-full max-w-6xl px-5 py-12">
        <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-sm">
            <Logo />
            <p className="mt-4 text-pretty text-sm leading-relaxed text-ink-500">
              Order ahead. It&rsquo;ll be ready when you arrive. Pickup only —
              you pay at the counter, nothing is delivered.
            </p>
          </div>

          <div className="flex flex-col gap-6 sm:flex-row sm:gap-16">
            <nav aria-label="For customers">
              <h2 className="text-xs font-semibold tracking-[0.14em] text-ink-400 uppercase">
                For customers
              </h2>
              <ul className="mt-3 space-y-2 text-sm text-ink-600">
                <li>
                  <Link
                    href="/explore"
                    className="transition hover:text-ink-900"
                  >
                    1 · Choose a destination
                  </Link>
                </li>
                <li>
                  <Link
                    href="/explore"
                    className="transition hover:text-ink-900"
                  >
                    2 · Pick an arrival time
                  </Link>
                </li>
                <li>
                  <Link
                    href="/orders"
                    className="transition hover:text-ink-900"
                  >
                    3 · Track your order
                  </Link>
                </li>
              </ul>
            </nav>
            <nav aria-label="For cafés">
              <h2 className="text-xs font-semibold tracking-[0.14em] text-ink-400 uppercase">
                For cafés
              </h2>
              <ul className="mt-3 space-y-2 text-sm text-ink-600">
                <li>
                  <Link
                    href="/merchant"
                    className="transition hover:text-ink-900"
                  >
                    Pickup board
                  </Link>
                </li>
                <li>
                  <Link
                    href="/merchant"
                    className="transition hover:text-ink-900"
                  >
                    Why ReadyBy?
                  </Link>
                </li>
                <li>
                  <Link
                    href="/login"
                    className="transition hover:text-ink-900"
                  >
                    Café sign-in
                  </Link>
                </li>
              </ul>
            </nav>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-4 border-t border-ink-100 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-ink-400">
            Demo cafés and sample data. Built to validate the idea with café
            owners.
          </p>
          <Button
            variant="ghost"
            size="sm"
            onClick={reset}
            className="self-start text-ink-500"
          >
            <RotateCcw className="size-3.5" aria-hidden />
            Clear my basket
          </Button>
        </div>
      </div>
    </footer>
  );
}