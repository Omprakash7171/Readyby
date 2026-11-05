import type { ReactNode } from "react";
import { cn } from "@/lib/format";

type Tone =
  | "neutral"
  | "brand"
  | "ready"
  | "warning"
  | "danger"
  | "info"
  | "dark";

const tones: Record<Tone, string> = {
  neutral: "bg-ink-100 text-ink-700 ring-ink-200/70",
  brand: "bg-brand-50 text-brand-700 ring-brand-200/70",
  ready: "bg-ready-50 text-ready-700 ring-ready-200",
  warning: "bg-amber-50 text-amber-700 ring-amber-200",
  danger: "bg-red-50 text-red-600 ring-red-200",
  info: "bg-sky-50 text-sky-700 ring-sky-200",
  dark: "bg-ink-900 text-white ring-ink-900/10",
};

interface BadgeProps {
  tone?: Tone;
  className?: string;
  children: ReactNode;
  /** Renders a small leading dot — handy for open/closed states. */
  dot?: boolean;
}

export function Badge({
  tone = "neutral",
  className,
  children,
  dot,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium tracking-[-0.01em] ring-1 ring-inset",
        tones[tone],
        className,
      )}
    >
      {dot ? (
        <span
          aria-hidden
          className="size-1.5 rounded-full bg-current opacity-70"
        />
      ) : null}
      {children}
    </span>
  );
}

const dotTones: Record<Tone, string> = {
  neutral: "bg-ink-400",
  brand: "bg-brand-500",
  ready: "bg-ready-500",
  warning: "bg-amber-500",
  danger: "bg-red-500",
  info: "bg-sky-500",
  dark: "bg-ink-900",
};

export function StatusDot({
  tone = "neutral",
  pulse,
  className,
}: {
  tone?: Tone;
  pulse?: boolean;
  className?: string;
}) {
  return (
    <span className={cn("relative inline-flex size-2", className)}>
      {pulse ? (
        <span
          className={cn(
            "absolute inline-flex h-full w-full animate-ping rounded-full opacity-60",
            dotTones[tone],
          )}
        />
      ) : null}
      <span className={cn("relative inline-flex size-2 rounded-full", dotTones[tone])} />
    </span>
  );
}