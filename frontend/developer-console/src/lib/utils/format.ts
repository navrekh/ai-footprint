export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(date);
}

/**
 * Formats a single measured value without implying more precision than the
 * backend provides. This only ever reduces trailing noise (e.g. a huge
 * value doesn't need 3 decimal places); it must never drop a decimal place
 * the backend actually reported for an ordinary-magnitude value like
 * 428.3 — rounding "428.3–512.7" down to "428–513" would silently discard
 * real precision the API supplied. Never scientific notation.
 */
export function formatMetricValue(value: number): string {
  const magnitude = Math.abs(value);
  const maximumFractionDigits = magnitude >= 1000 ? 0 : magnitude >= 1 ? 1 : 3;
  return new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(value);
}

/**
 * Formats a min/max pair as a range ("42.8–51.2"), or a single value when
 * min and max are equal (an exact, backend-supplied point value) — never
 * an average, and never invoked when either bound is null/missing.
 */
export function formatRange(min: number, max: number): string {
  if (min === max) return formatMetricValue(min);
  return `${formatMetricValue(min)}–${formatMetricValue(max)}`;
}
