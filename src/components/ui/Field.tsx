import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/format";

interface FieldProps {
  label: string;
  hint?: string;
  htmlFor: string;
  children: ReactNode;
  className?: string;
}

export function Field({ label, hint, htmlFor, children, className }: FieldProps) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <label
        htmlFor={htmlFor}
        className="text-sm font-medium text-ink-700"
      >
        {label}
      </label>
      {children}
      {hint ? <p className="text-xs text-ink-400">{hint}</p> : null}
    </div>
  );
}

const controlBase =
  "w-full rounded-2xl border border-ink-200 bg-white px-4 text-ink-900 placeholder:text-ink-300 transition focus:border-brand-400 focus:ring-4 focus:ring-brand-500/10 focus:outline-none";

export function Input({
  className,
  ...props
}: ComponentProps<"input">) {
  return (
    <input
      className={cn(controlBase, "h-12", className)}
      {...props}
    />
  );
}

export function Textarea({
  className,
  ...props
}: ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(controlBase, "min-h-24 py-3", className)}
      {...props}
    />
  );
}

export function Select({
  className,
  children,
  ...props
}: ComponentProps<"select">) {
  return (
    <select
      className={cn(controlBase, "h-12 appearance-none pr-10", className)}
      {...props}
    >
      {children}
    </select>
  );
}