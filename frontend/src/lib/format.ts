// Simple formatting utilities
export const formatRupees = (value: number | null | undefined, scale: 'default' | 'millions' | 'billions' = 'default'): string => {
  if (value === null || value === undefined) return '—';

  const scaled = scale === 'millions' ? value / 1e6 : scale === 'billions' ? value / 1e9 : value;
  const decimals = scale === 'default' ? 2 : scale === 'billions' ? 1 : 0;
  const suffix = scale === 'millions' ? 'M' : scale === 'billions' ? 'B' : '';

  return `Rs. ${scaled.toFixed(decimals)}${suffix}`;
};

export const formatPercent = (value: number | null | undefined, decimals = 1): string => {
  if (value === null || value === undefined) return '—';
  return `${value > 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

export const formatRatio = (value: number | null | undefined, decimals = 2): string => {
  if (value === null || value === undefined) return '—';
  return `${value.toFixed(decimals)}x`;
};

export function formatPrice(value: number | null): string {
  return value != null ? `PKR ${value.toFixed(2)}` : "—";
}

export function formatPct(value: number | null): string {
  return value != null ? `${value >= 0 ? "+" : ""}${value.toFixed(2)}%` : "—";
}

export function formatMarketCap(value: number | null): string {
  return value != null ? `PKR ${(value / 1_000_000).toFixed(1)} bn` : "—";
}

export function formatMultiple(value: number | null, digits = 2): string {
  return value != null ? `${value.toFixed(digits)}x` : "—";
}

export function formatLiveRatio(value: number | null, digits = 2, unit: "x" | "%" = "%"): string {
  if (value == null || value === 0) return "—";
  return unit === "x" ? formatMultiple(value, digits) : formatPercent(value, digits);
}
