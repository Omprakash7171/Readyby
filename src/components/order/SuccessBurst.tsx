"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/format";

/** Celebratory check used on the confirmation screen. Deliberately small. */
export function SuccessBurst({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative mx-auto grid size-28 place-items-center sm:size-32",
        className,
      )}
    >
      <span
        aria-hidden
        className="absolute inset-0 animate-ping rounded-full bg-ready-400/20 [animation-duration:2.4s]"
      />
      <span
        aria-hidden
        className="absolute inset-3 rounded-full bg-ready-50 ring-1 ring-ready-200"
      />
      <span
        aria-hidden
        className="absolute inset-0 rounded-full border-2 border-dashed border-ready-300/60 animate-[spin_28s_linear_infinite]"
      />
      <span className="animate-pop-check relative grid size-14 place-items-center rounded-full bg-ready-500 text-white shadow-[0_12px_30px_-10px_rgba(5,150,105,0.85)] sm:size-16">
        <Check className="size-8" strokeWidth={3} aria-hidden />
      </span>
      <span className="sr-only">Order confirmed</span>
    </div>
  );
}