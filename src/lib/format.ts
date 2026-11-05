/** Joins conditional class names. Keeps the project dependency-free. */
export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

const gbp = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  minimumFractionDigits: 2,
});

export function formatPrice(value: number) {
  return gbp.format(value);
}

/** Minutes -> metres using an average 80 m/min walking pace. */
export function minutesToMetres(minutes: number) {
  return Math.round(minutes * 80);
}

/** Metres -> whole walking minutes (never below 1). */
export function metresToMinutes(metres: number) {
  return Math.max(1, Math.round(metres / 80));
}

export function formatDistance(metres: number) {
  return `${metres} m`;
}

export function pluralise(count: number, singular: string, plural?: string) {
  return count === 1 ? singular : (plural ?? `${singular}s`);
}