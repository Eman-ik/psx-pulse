/** Shared formatters for the comparison-style tables (Companies, Screener, Competitors tab) —
 * previously copy-pasted three times with slightly different signatures.
 */

export function formatPrice(v: number | null): string {
  return v != null ? `PKR ${v.toFixed(2)}` : "—";
}

export function formatPct(v: number | null): string {
  return v != null ? `${v >= 0 ? "+" : ""}${v.toFixed(2)}%` : "—";
}

export function formatMarketCap(v: number | null): string {
  return v != null ? `PKR ${(v / 1_000_000).toFixed(1)} bn` : "—";
}

export function formatMultiple(v: number | null, digits = 2): string {
  return v != null ? `${v.toFixed(digits)}x` : "—";
}

export function formatPercent(v: number | null, digits = 1): string {
  return v != null ? `${v.toFixed(digits)}%` : "—";
}

/** pe_ratio/dividend_yield come straight from psxdata's live quote, where exactly 0 usually
 * means "not available" rather than a genuine zero — treat it the same as null. Only applies
 * to those two live-quote-sourced fields, not to our own calculated ratios (ROE, D/E, etc.),
 * where 0 is a plausible real value.
 */
export function formatLiveRatio(v: number | null, digits = 2, unit: "x" | "%" = "%"): string {
  if (v == null || v === 0) return "—";
  return unit === "x" ? formatMultiple(v, digits) : formatPercent(v, digits);
}
