import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/format";

type Variant =
  | "primary"
  | "dark"
  | "secondary"
  | "outline"
  | "ghost"
  | "success"
  | "danger";
type Size = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-medium tracking-[-0.01em] transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98] select-none whitespace-nowrap";

const variants: Record<Variant, string> = {
  primary:
    "bg-brand-500 text-white shadow-[0_8px_20px_-10px_rgba(193,69,31,0.9)] hover:bg-brand-600 hover:shadow-[0_12px_26px_-10px_rgba(163,53,26,0.85)] hover:-translate-y-px",
  dark: "bg-ink-900 text-white hover:bg-ink-800 hover:-translate-y-px",
  secondary:
    "bg-crema-100 text-ink-800 hover:bg-crema-200 border border-ink-100",
  outline:
    "border border-ink-200 bg-white text-ink-800 hover:border-ink-400 hover:bg-ink-50",
  ghost: "text-ink-600 hover:bg-ink-100 hover:text-ink-900",
  success:
    "bg-ready-600 text-white shadow-[0_8px_20px_-10px_rgba(5,150,105,0.9)] hover:bg-ready-700 hover:-translate-y-px",
  danger:
    "border border-red-200 bg-white text-red-600 hover:border-red-400 hover:bg-red-50",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-4 text-sm",
  md: "h-11 px-5 text-[0.95rem]",
  lg: "h-13 px-7 text-base",
};

interface CommonProps {
  variant?: Variant;
  size?: Size;
  className?: string;
  children: ReactNode;
  fullWidth?: boolean;
}

type ButtonProps = CommonProps & Omit<ComponentProps<"button">, "className">;
type ButtonLinkProps = CommonProps &
  Omit<ComponentProps<typeof Link>, "className"> & { href: string };

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  fullWidth,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        base,
        variants[variant],
        sizes[size],
        fullWidth && "w-full",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  children,
  fullWidth,
  ...props
}: ButtonLinkProps) {
  return (
    <Link
      className={cn(
        base,
        variants[variant],
        sizes[size],
        fullWidth && "w-full",
        className,
      )}
      {...props}
    >
      {children}
    </Link>
  );
}

/**
 * Anchor styled as a button, for in-page jumps such as "See how it works".
 * Kept separate from `ButtonLink` so navigation links stay real `Link`s.
 */
export function ButtonAnchor({
  variant = "primary",
  size = "md",
  className,
  children,
  fullWidth,
  ...props
}: CommonProps & ComponentProps<"a">) {
  return (
    <a
      className={cn(
        base,
        variants[variant],
        sizes[size],
        fullWidth && "w-full",
        className,
      )}
      {...props}
    >
      {children}
    </a>
  );
}

export function IconButton({
  label,
  className,
  children,
  ...props
}: Omit<ButtonProps, "size" | "variant"> & { label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex h-10 w-10 items-center justify-center rounded-full border border-ink-200 bg-white text-ink-700 transition hover:border-ink-400 hover:bg-ink-50 active:scale-95",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}