import { Clock, MapPin, Star } from "lucide-react";
import { cn, formatDistance } from "@/lib/format";
import { Badge, StatusDot } from "@/components/ui/Badge";

export function Stars({
  rating,
  className,
  showValue = true,
}: {
  rating: number;
  className?: string;
  showValue?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <span className="inline-flex items-center gap-0.5" aria-hidden>
        {Array.from({ length: 5 }, (_, index) => {
          const fill = Math.min(1, Math.max(0, rating - index));
          return (
            <span key={index} className="relative inline-block size-3.5">
              <Star className="absolute inset-0 size-3.5 text-ink-200" fill="currentColor" />
              <span
                className="absolute inset-0 overflow-hidden"
                style={{ width: `${fill * 100}%` }}
              >
                <Star
                  className="size-3.5 text-amber-400"
                  fill="currentColor"
                />
              </span>
            </span>
          );
        })}
      </span>
      {showValue ? (
        <span className="text-sm font-semibold text-ink-800 tabular-nums">
          {rating.toFixed(1)}
        </span>
      ) : (
        <span className="sr-only">{rating.toFixed(1)} out of 5</span>
      )}
    </span>
  );
}

const openTone = {
  open: { badge: "ready" as const, label: "Open", dot: "ready" as const },
  "closing-soon": {
    badge: "warning" as const,
    label: "Closing soon",
    dot: "warning" as const,
  },
  closed: { badge: "neutral" as const, label: "Closed", dot: "neutral" as const },
};

export function OpenBadge({
  state,
  hours,
  className,
}: {
  /** The API's open state, or null when the café has no availability yet. */
  state: "open" | "closing-soon" | "closed" | null;
  hours?: string;
  className?: string;
}) {
  const tone = state ? openTone[state] : openTone.closed;
  return (
    <Badge tone={tone.badge} className={className}>
      <StatusDot tone={tone.dot} pulse={state === "open"} />
      {hours ?? tone.label}
    </Badge>
  );
}

export function MetaRow({
  distanceMetres,
  walkMinutes,
  className,
}: {
  distanceMetres: number | null;
  walkMinutes: number | null;
  className?: string;
}) {
  if (distanceMetres === null && walkMinutes === null) return null;

  return (
    <span className={cn("inline-flex items-center gap-3 text-sm text-ink-500", className)}>
      {distanceMetres !== null ? (
        <span className="inline-flex items-center gap-1.5">
          <MapPin className="size-3.5 text-ink-400" aria-hidden />
          {formatDistance(distanceMetres)}
        </span>
      ) : null}
      {distanceMetres !== null && walkMinutes !== null ? (
        <span aria-hidden className="size-1 rounded-full bg-ink-300" />
      ) : null}
      {walkMinutes !== null ? (
        <span className="inline-flex items-center gap-1.5">
          <Clock className="size-3.5 text-ink-400" aria-hidden />
          {walkMinutes} min walk
        </span>
      ) : null}
    </span>
  );
}