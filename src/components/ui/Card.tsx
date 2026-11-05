import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/format";

interface CardProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  /** Adds a hover lift — use for cards that are themselves interactive. */
  interactive?: boolean;
  as?: "div" | "li" | "article" | "section";
}

export function Card({
  children,
  className,
  style,
  interactive,
  as: Tag = "div",
}: CardProps) {
  return (
    <Tag
      style={style}
      className={cn(
        "rounded-3xl border border-ink-100 bg-white shadow-soft",
        interactive &&
          "transition-all duration-300 hover:-translate-y-1 hover:border-ink-200 hover:shadow-lift",
        className,
      )}
    >
      {children}
    </Tag>
  );
}

export function Section({
  children,
  className,
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn("px-5 py-16 sm:py-24", className)}>
      <div className="mx-auto w-full max-w-6xl">{children}</div>
    </section>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "center",
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  align?: "center" | "left";
  className?: string;
}) {
  return (
    <div
      className={cn(
        align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl",
        className,
      )}
    >
      {eyebrow ? (
        <p className="mb-3 text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
          {eyebrow}
        </p>
      ) : null}
      <h2 className="text-balance text-3xl font-semibold tracking-[-0.03em] text-ink-900 sm:text-4xl">
        {title}
      </h2>
      {description ? (
        <p className="mt-4 text-pretty text-base leading-relaxed text-ink-500 sm:text-lg">
          {description}
        </p>
      ) : null}
    </div>
  );
}