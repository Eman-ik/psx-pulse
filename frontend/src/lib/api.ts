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

export interface CompanyListItem {
  id: number;
  name: string;
  short_name: string | null;
  sector_id: number | null;
  symbol: string | null;
}

export interface FinancialFactPoint {
  period_end: string;
  period_type: string;
  value: number;
  unit: string;
  is_restated: boolean;
}

export interface RatioSeries {
  name: string;
  category: string;
  unit: string;
  values: { period_end: string; value: number }[];
}

export interface CompanyOverview {
  issuer: {
    id: number;
    name: string;
    short_name: string | null;
    sector_id: number | null;
    business_description: string | null;
    address: string | null;
    website: string | null;
    registrar: string | null;
    auditor: string | null;
    fiscal_year_end_month: number | null;
    is_conglomerate: boolean;
  };
  symbol: string | null;
  free_float_pct: number | null;
  parent_chain: { id: number; name: string; is_psx_listed: boolean }[];
  subsidiaries: { id: number; name: string }[];
  board: { full_name: string; role: string }[];
  live_quote: LiveQuote | null;
  financials: Record<string, FinancialFactPoint[]>;
  ratios: Record<string, RatioSeries>;
  payouts: { action_type: string; effective_date: string; ratio_or_amount: number | null }[];
  announcements: { id: number; title: string; category: string; published_at: string }[];
  sources: { document_type: string; source_tier: string; url: string | null; fetched_at: string }[];
  operational_metrics: Record<string, { product: string | null; period_end: string; value: number; unit: string }[]>;
  thesis: {
    as_of_date: string;
    bull_case: string;
    base_case: string;
    bear_case: string;
    key_catalysts: string[];
    key_risks: string[];
    author: string;
  } | null;
  subsidiary_contributions: {
    subsidiary_id: number;
    subsidiary_name: string;
    line_item: string;
    period_end: string;
    subsidiary_value: number;
    parent_value: number;
    contribution_pct: number;
  }[];
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

export async function fetchCompanies(): Promise<CompanyListItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies`, { cache: "no-store" });
    if (!res.ok) return [];
    return (await res.json()) as CompanyListItem[];
  } catch {
    return [];
  }
}

export async function fetchCompanyOverview(issuerId: number): Promise<CompanyOverview | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies/${issuerId}/overview`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as CompanyOverview;
  } catch {
    return null;
  }
}
