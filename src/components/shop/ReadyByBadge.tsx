import { Clock } from "lucide-react";
import { cn } from "@/lib/format";

/**
 * The most repeated piece of feedback in the product: "this will be finished
 * by the time you arrive". Both clock times are computed by the API for the
 * selected arrival time, so this component never derives anything itself.
 */
export function ReadyByBadge({
  readyLabel,
  startLabel,
  className,
  size = "md",
}: {
  readyLabel: string;
  startLabel?: string | null;
  className?: string;
  size?: "sm" | "md";
}) {
  return (
    <p
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full bg-brand-50 font-semibold text-brand-800",
        size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm",
        className,
      )}
    >
      <Clock className="size-3.5 shrink-0" aria-hidden />
      Ready by {readyLabel}
      {startLabel ? <span className="sr-only">, starting around {startLabel}</span> : null}
    </p>
  );
}