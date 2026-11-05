"use client";

import { Check, Clock, LoaderCircle, Sparkles, Zap } from "lucide-react";
import { useMemo } from "react";
import type { PickupSlot } from "@/lib/apiTypes";
import { cn } from "@/lib/format";
import { useBooking } from "@/context/BookingProvider";
import { buildPickupOptions, type PickupOption } from "@/lib/pickup";

interface PickupTimeSelectorProps {
  /**
   * One café's server-computed plan for the chosen arrival time. When present,
   * the selector shows the times the café itself reported rather than anything
   * derived in the browser.
   */
  cafe?: {
    name: string;
    start_preparing_time_label: string | null;
    estimated_ready_time_label: string | null;
  } | null;
  slots?: PickupSlot[] | null;
  notice?: string | null;
  loading?: boolean;
  heading?: string;
  description?: string;
  className?: string;
}

export function PickupTimeSelector({
  cafe,
  slots,
  notice,
  loading,
  heading = "When will you arrive?",
  description = "Pick the time you\u2019ll walk in. Your order will be ready the moment you arrive.",
  className,
}: PickupTimeSelectorProps) {
  const { arrivalAt, selectArrival, hasArrival } = useBooking();

  const options = useMemo(() => {
    if (slots?.length) {
      return slots.map<PickupOption>((slot) => {
        const at = new Date(slot.arrival_time).getTime();
        return {
          id: slot.arrival_time,
          label: slot.time_label,
          hint: `${slot.day_label} \u00b7 ${
            slot.remaining === 1 ? "1 spot left" : `${slot.remaining} spots left`
          }`,
          isAsap: false,
          offsetMinutes: 0,
          at,
        };
      });
    }
    return buildPickupOptions();
  }, [slots]);

  return (
    <fieldset className={className}>
      <legend className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
        {heading}
      </legend>
      <p className="mt-1 text-pretty text-sm text-ink-500">{description}</p>

      {notice ? (
        <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-sm text-amber-800">
          {notice}
        </p>
      ) : null}

      <div
        role="radiogroup"
        aria-label="Arrival time"
        className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-3"
      >
        {options.map((option) => (
          <PickupOptionButton
            key={option.id}
            option={option}
            selected={option.at === arrivalAt}
            onSelect={() => selectArrival(option.at)}
          />
        ))}
      </div>

      {loading ? (
        <p className="mt-3.5 flex items-center gap-2 text-sm text-ink-500">
          <LoaderCircle className="size-4 animate-spin" aria-hidden />
          Checking this café&rsquo;s kitchen for your time...
        </p>
      ) : !hasArrival ? (
        <p className="mt-3.5 text-sm text-ink-500">Choose a time to see what cafés can serve it.</p>
      ) : null}

      <ReadyByPlanNote cafe={cafe ?? null} />
    </fieldset>
  );
}

function PickupOptionButton({
  option,
  selected,
  onSelect,
}: {
  option: PickupOption;
  selected: boolean;
  onSelect: () => void;
}) {
  const Icon = option.isAsap ? Zap : Clock;

  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={cn(
        "group relative flex flex-col items-start gap-0.5 rounded-2xl border p-3.5 text-left transition-all duration-200",
        selected
          ? "border-brand-400 bg-brand-50 shadow-[0_10px_24px_-16px_rgba(193,69,31,0.8)]"
          : "border-ink-200 bg-white hover:border-ink-400 hover:bg-ink-50",
      )}
    >
      <span className="flex w-full items-center justify-between gap-2">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 text-[0.95rem] font-semibold",
            selected ? "text-brand-700" : "text-ink-900",
          )}
        >
          <Icon className="size-4" aria-hidden />
          {option.label}
        </span>
        <span
          aria-hidden
          className={cn(
            "grid size-4.5 shrink-0 place-items-center rounded-full border transition",
            selected ? "border-brand-500 bg-brand-500" : "border-ink-300 group-hover:border-ink-400",
          )}
        >
          {selected ? <Check className="size-3 text-white" strokeWidth={3} /> : null}
        </span>
      </span>
      <span
        className={cn("text-xs leading-snug", selected ? "text-brand-700/80" : "text-ink-500")}
      >
        {option.hint}
      </span>
    </button>
  );
}

/**
 * A single café's server-computed timing, shown under the arrival picker. Every
 * value here came from the API for the exact arrival time that is selected.
 */
export function ReadyByPlanNote({
  cafe,
}: {
  cafe: {
    name: string;
    start_preparing_time_label: string | null;
    estimated_ready_time_label: string | null;
  } | null;
}) {
  if (!cafe || !cafe.estimated_ready_time_label) return null;

  return (
    <p className="mt-3.5 flex items-start gap-2 rounded-2xl bg-brand-50 px-3.5 py-3 text-sm text-brand-900">
      <Sparkles className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden />
      <span>
        <strong className="font-semibold">{cafe.name}</strong> will have it ready by{" "}
        <strong className="font-semibold">{cafe.estimated_ready_time_label}</strong>
        {cafe.start_preparing_time_label ? (
          <>
            {" "}
            and start preparing around{" "}
            <strong className="font-semibold">{cafe.start_preparing_time_label}</strong>
          </>
        ) : null}
        .
      </span>
    </p>
  );
}