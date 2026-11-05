import type { ReactNode } from "react";
import { cn } from "@/lib/format";
import { ButtonLink } from "@/components/ui/Button";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  actionHref,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center rounded-3xl border border-dashed border-ink-200 bg-white/60 px-6 py-14 text-center",
        className,
      )}
    >
      {icon ? (
        <div
          aria-hidden
          className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-crema-100 text-ink-400"
        >
          {icon}
        </div>
      ) : null}
      <h3 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
        {title}
      </h3>
      <p className="mt-2 max-w-sm text-pretty text-sm leading-relaxed text-ink-500">
        {description}
      </p>
      {actionLabel && actionHref ? (
        <ButtonLink href={actionHref} className="mt-6" variant="dark">
          {actionLabel}
        </ButtonLink>
      ) : null}
    </div>
  );
}