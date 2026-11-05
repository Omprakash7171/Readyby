/**
 * Arrival-time slots.
 *
 * The browser only offers times; the server decides which of them a café can
 * actually serve (`can_order` / `unavailable_reason` on every café payload).
 */

export const ASAP_PREP_MINUTES = 10;

/** How long an "as soon as possible" order takes the customer to walk over. */
export const ASAP_ARRIVAL_MINUTES = 15;

export interface PickupOption {
  id: string;
  /** Label shown on the button, e.g. "ASAP" or "10:15 AM". */
  label: string;
  /** Supporting line, e.g. "In about 15 min". */
  hint: string;
  isAsap: boolean;
  offsetMinutes: number;
  /** Epoch ms of the arrival this option represents. */
  at: number;
}

/** Formats a date as an unambiguous 12-hour clock, e.g. "10:15 AM". */
export function formatClockTime(date: Date) {
  return date
    .toLocaleTimeString("en-GB", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    })
    .replace(/[\u202f\u00a0]/g, " ")
    .replace(/\s*([ap])\.?\s*m\.?$/i, (_match, period) => ` ${String(period).toUpperCase()}M`)
    .trim();
}

function formatDayLabel(date: Date) {
  return date.toLocaleDateString("en-GB", { weekday: "short" });
}

function slotIsToday(slot: Date, now: Date) {
  return (
    slot.getFullYear() === now.getFullYear() &&
    slot.getMonth() === now.getMonth() &&
    slot.getDate() === now.getDate()
  );
}

/**
 * Builds the arrival options: an ASAP slot plus the next four 15-minute slots.
 * Each option carries the epoch it represents so the API request is exact and
 * the chosen time survives a refresh.
 */
export function buildPickupOptions(now = new Date()): PickupOption[] {
  const options: PickupOption[] = [
    {
      id: "asap",
      label: "ASAP",
      hint: `In about ${ASAP_ARRIVAL_MINUTES} min`,
      isAsap: true,
      offsetMinutes: ASAP_ARRIVAL_MINUTES,
      at: now.getTime() + ASAP_ARRIVAL_MINUTES * 60_000,
    },
  ];

  const start = new Date(now);
  start.setSeconds(0, 0);
  start.setMinutes(Math.ceil((start.getMinutes() + 1) / 15) * 15);

  for (let i = 0; i < 4; i += 1) {
    const slot = new Date(start.getTime() + i * 15 * 60_000);
    options.push({
      id: slot.toISOString(),
      label: formatClockTime(slot),
      hint: slotIsToday(slot, now) ? "Later today" : formatDayLabel(slot),
      isAsap: false,
      offsetMinutes: Math.round((slot.getTime() - now.getTime()) / 60_000),
      at: slot.getTime(),
    });
  }

  return options;
}

/** Whole minutes until the customer is due to walk in. */
export function minutesUntil(arrivalAt: number, now = Date.now()) {
  return Math.max(0, Math.round((arrivalAt - now) / 60_000));
}