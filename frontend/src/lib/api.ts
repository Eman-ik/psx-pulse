export interface LiveQuote {
  symbol: string;
  name: string;
  price: number | null;
  change_pct: number | null;
  change_1y_pct: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  day_open: number | null;
  day_high: number | null;
  day_low: number | null;
  day_close: number | null;
  volume: number | null;
  as_of_date: string | null;
  circuit_upper: number | null;
  circuit_lower: number | null;
}

export interface LiveQuotesResponse {
  data_source: string;
  disclaimer: string;
  fetched_at: string;
  quotes: LiveQuote[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Fetches live-ish PSX quotes from the backend (psxdata-sourced, see docs/source_registry.yaml).
 * Returns null on any failure so the dashboard can fall back to sample data instead of crashing —
 * this is a dev-only scraper-backed source with no uptime guarantee.
 */
export async function fetchLiveQuotes(): Promise<LiveQuotesResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/market/live`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as LiveQuotesResponse;
  } catch {
    return null;
  }
}
