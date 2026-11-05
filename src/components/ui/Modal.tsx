"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "@/lib/format";
import { IconButton } from "@/components/ui/Button";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  /** `right` slides a panel in from the side; `center` centres a dialog. */
  placement?: "center" | "right";
  size?: "md" | "lg";
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  placement = "center",
  size = "md",
}: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    const previousOverflow = document.body.style.overflow;
    const previousActive = document.activeElement as HTMLElement | null;

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    panelRef.current?.focus();

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      previousActive?.focus?.();
    };
  }, [open, onClose]);

  if (!open || typeof document === "undefined") return null;

  const isPanel = placement === "right";

  return createPortal(
    <div className="fixed inset-0 z-50 flex" role="presentation">
      <button
        type="button"
        aria-label="Close dialog"
        onClick={onClose}
        className="absolute inset-0 animate-fade-in bg-ink-950/40 backdrop-blur-[2px]"
      />
      <div
        className={cn(
          "relative z-10 flex w-full",
          isPanel
            ? "max-w-md justify-end sm:max-w-md"
            : "items-end justify-center sm:items-center",
        )}
      >
        <div
          ref={panelRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          aria-describedby={description ? descriptionId : undefined}
          tabIndex={-1}
          className={cn(
            "flex max-h-[92dvh] w-full flex-col overflow-hidden bg-white shadow-pop outline-none",
            isPanel
              ? "h-full animate-slide-left rounded-l-3xl sm:rounded-l-none"
              : cn(
                  "animate-scale-in rounded-t-3xl sm:rounded-3xl",
                  size === "lg" ? "sm:max-w-2xl" : "sm:max-w-md",
                ),
          )}
        >
          <header className="flex items-start justify-between gap-4 border-b border-ink-100 px-5 py-4 sm:px-6">
            <div className="min-w-0">
              <h2
                id={titleId}
                className="truncate text-lg font-semibold tracking-[-0.02em] text-ink-900"
              >
                {title}
              </h2>
              {description ? (
                <p
                  id={descriptionId}
                  className="mt-0.5 text-sm text-ink-500"
                >
                  {description}
                </p>
              ) : null}
            </div>
            <IconButton label="Close" onClick={onClose} className="shrink-0">
              <X className="size-4" aria-hidden />
            </IconButton>
          </header>

          <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5 sm:px-6">
            {children}
          </div>

          {footer ? (
            <footer className="border-t border-ink-100 bg-crema-50 px-5 py-4 sm:px-6">
              {footer}
            </footer>
          ) : null}
        </div>
      </div>
    </div>,
    document.body,
  );
}