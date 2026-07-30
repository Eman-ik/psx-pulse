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
  scope: string;
  value: number;
  unit: string;
  is_restated: boolean;
}

export interface RatioSeries {
  name: string;
  category: string;
  unit: string;
  formula: string;
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
    establishment_year: number | null;
  };
  data_delay_notice: string;
  symbol: string | null;
  security_id: number | null;
  listing_status: string | null;
  free_float_pct: number | null;
  beta: {
    value: number;
    as_of_date: string;
    is_issuer_specific: boolean;
    source_note: string;
  } | null;
  parent_chain: { id: number; name: string; is_psx_listed: boolean }[];
  subsidiaries: { id: number; name: string }[];
  board: { full_name: string; role: string }[];
  live_quote: LiveQuote | null;
  financials: Record<string, FinancialFactPoint[]>;
  ratios: Record<string, RatioSeries>;
  payouts: { action_type: string; effective_date: string; ratio_or_amount: number | null }[];
  announcements: {
    id: number;
    title: string;
    category: string;
    published_at: string;
    summary: string | null;
    sentiment_score: number | null;
    source_url: string | null;
  }[];
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

export interface ComparisonRow {
  id: number;
  symbol: string | null;
  name: string;
  price: number | null;
  change_pct: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  roe: number | null;
  debt_to_equity: number | null;
}

export interface RiskSnapshot {
  as_of_date: string;
  overall_risk: "LOW" | "MODERATE" | "ELEVATED" | "HIGH";
  geopolitical: string;
  economy: string;
  imf_program: string;
  currency_pkr: string;
  key_positives: string[];
  key_negatives: string[];
}

export interface NewsAnnouncement {
  id: number;
  issuer_id: number | null;
  title: string;
  category: string;
  published_at: string;
  summary: string | null;
  sentiment_score: number | null;
  source_url: string | null;
}

export interface SectorCompany {
  id: number;
  name: string;
  symbol: string | null;
}

export interface FertilizerSector {
  sector_name: string;
  psx_sector_code: string | null;
  company_count: number;
  companies: SectorCompany[];
  aggregate_market_cap_pkr: number | null;
  companies_with_market_cap: number;
  avg_capacity_utilization_pct: number | null;
  companies_with_utilization_data: number;
  total_production_volume: number | null;
  companies_with_production_data: number;
  not_available: string[];
}

export interface CementSector {
  sector_name: string;
  psx_sector_code: string | null;
  company_count: number;
  companies: SectorCompany[];
  aggregate_market_cap_pkr: number | null;
  companies_with_market_cap: number;
  avg_capacity_utilization_pct: number | null;
  companies_with_utilization_data: number;
  not_available: string[];
}

export interface PriceBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
  is_delayed: boolean;
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

export interface RatioBenchmark {
  mean: number;
  count: number;
}

export async function fetchRatioBenchmarks(): Promise<Record<string, RatioBenchmark>> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies/ratio-benchmarks`, { cache: "no-store" });
    if (!res.ok) return {};
    return (await res.json()) as Record<string, RatioBenchmark>;
  } catch {
    return {};
  }
}

export async function fetchComparison(): Promise<ComparisonRow[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies/comparison`, { cache: "no-store" });
    if (!res.ok) return [];
    return (await res.json()) as ComparisonRow[];
  } catch {
    return [];
  }
}

export async function fetchRiskSnapshot(): Promise<RiskSnapshot | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/macro/risk-snapshot`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as RiskSnapshot | null;
  } catch {
    return null;
  }
}

export async function fetchNewsAnnouncements(): Promise<NewsAnnouncement[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/news/announcements`, { cache: "no-store" });
    if (!res.ok) return [];
    return (await res.json()) as NewsAnnouncement[];
  } catch {
    return [];
  }
}

export async function fetchFertilizerSector(): Promise<FertilizerSector | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/sectors/fertilizer`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as FertilizerSector;
  } catch {
    return null;
  }
}

export async function fetchCementSector(): Promise<CementSector | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/sectors/cement`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as CementSector;
  } catch {
    return null;
  }
}

export async function fetchCementLiveQuotes(): Promise<LiveQuotesResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/market/live/cement`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as LiveQuotesResponse;
  } catch {
    return null;
  }
}

export interface PricesResponse {
  adjusted: boolean;
  adjustment_methodology?: string;
  corporate_actions_on_file?: number;
  delayed_data_notice: string;
  bars: PriceBar[];
}

export async function fetchPrices(securityId: number, adjusted = false): Promise<PricesResponse> {
  const empty: PricesResponse = { adjusted, delayed_data_notice: "", bars: [] };
  try {
    const res = await fetch(`${API_BASE_URL}/market/${securityId}/prices?adjusted=${adjusted}`, {
      cache: "no-store",
    });
    if (!res.ok) return empty;
    return (await res.json()) as PricesResponse;
  } catch {
    return empty;
  }
}

export interface IndexPrices {
  code: string;
  name: string;
  delayed_data_notice: string;
  bars: PriceBar[];
}

export async function fetchIndexPrices(code: string): Promise<IndexPrices | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/market/index/${code}/prices`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as IndexPrices | null;
  } catch {
    return null;
  }
}

export interface SignalResearch {
  is_research_only: true;
  composite_signal: string;
  disclaimer?: string;
  reason?: string;
  as_of_date?: string;
  quality_score: number | null;
  growth_score: number | null;
  financial_health_score: number | null;
  valuation_score: number | null;
  catalyst_risk_score: number | null;
  momentum_score: number | null;
  risk_score: number | null;
  policy_version?: number;
  suppressed?: boolean;
  suppression_reasons?: string[] | null;
}

export async function fetchSignalResearch(issuerId: number): Promise<SignalResearch | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/signals/research/${issuerId}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as SignalResearch;
  } catch {
    return null;
  }
}
