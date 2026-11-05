import { cn } from "@/lib/format";

/**
 * ReadyBy logotype — a check-mark inside a rounded tile reads as "ready" at a
 * glance and stays legible at navbar size.
 */
export function Logo({
  className,
  size = "md",
  showWordmark = true,
}: {
  className?: string;
  size?: "sm" | "md" | "lg";
  showWordmark?: boolean;
}) {
  const tile = {
    sm: "size-7 rounded-[0.55rem]",
    md: "size-8 rounded-[0.7rem]",
    lg: "size-11 rounded-2xl",
  }[size];

  const text = {
    sm: "text-[1.05rem]",
    md: "text-[1.2rem]",
    lg: "text-2xl",
  }[size];

  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        aria-hidden
        className={cn(
          "relative grid place-items-center bg-ink-900 shadow-[0_6px_16px_-8px_rgba(12,10,8,0.9)]",
          tile,
        )}
      >
        <span className="absolute inset-0 rounded-[inherit] bg-gradient-to-br from-brand-400/25 to-transparent" />
        <svg viewBox="0 0 24 24" className="relative size-[60%]">
          <path
            d="M5 12.5 9.5 17 19 7.5"
            fill="none"
            stroke="white"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      {showWordmark ? (
        <span
          className={cn(
            "font-semibold tracking-[-0.035em] text-ink-900",
            text,
          )}
        >
          Ready<span className="text-brand-500">By</span>
        </span>
      ) : null}
    </span>
  );
}