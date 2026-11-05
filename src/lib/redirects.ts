/** A same-site path, or null for anything that could leave the site. */
export function safeNext(value: string | null | undefined): string | null {
  if (!value) return null;
  return value.startsWith("/") && !value.startsWith("//") ? value : null;
}

/** Where a signed-in customer should land; never a café-workspace page. */
export function customerDestination(value: string | null | undefined): string {
  const next = safeNext(value);
  if (!next || next === "/merchant" || next.startsWith("/merchant/")) {
    return "/explore";
  }
  return next;
}
