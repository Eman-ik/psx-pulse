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
  sector: string | null;
  price: number | null;
  change_pct: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  eps: number | null;
  dividend_per_share: number | null;
  /** "live" = live price + financials on file. "historical" = price history but no
   * live quote. "partial" = some financials but no price history. "unverified" = an
   * identity record only, no price or financial data yet. See comparison.py. */
  coverage_status: "live" | "historical" | "partial" | "unverified";
  roe: number | null;
  roa: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  net_profit_margin: number | null;
  revenue_growth_yoy: number | null;
  eps_growth_yoy: number | null;
  // Real, research-only scoring output (see score_disclaimer) -- null when this
  // issuer has no scoring run on file yet, never a placeholder.
  ai_signal: string | null;
  ai_score: number | null;
  ai_quality_score: number | null;
  ai_growth_score: number | null;
  ai_financial_health_score: number | null;
  ai_valuation_score: number | null;
  ai_momentum_score: number | null;
  ml_signal: string | null;
  ml_outperformance_probability: number | null;
  score_disclaimer: string | null;
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
 * Returns null on any failure (including timeout) so the dashboard can fall back to sample data
 * instead of crashing or hanging -- this is a dev-only scraper-backed source with no uptime
 * guarantee. Capped at 5s: this is still called during SSR (Dashboard, News -- pages whose live
 * data feeds real layout decisions, not just a table cell, so they weren't moved to the
 * client-side useLiveQuotes() pattern the Screener/Ranking/Companies/Sector/Company pages use).
 * Without this cap, this single call could block those pages' entire render for up to 35s (the
 * batch scrape's own cap, see psx_live.py) every time the underlying source is slow or blocked.
 */
export async function fetchLiveQuotes(): Promise<LiveQuotesResponse | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const res = await fetch(`${API_BASE_URL}/market/live`, { cache: "no-store", signal: controller.signal });
      if (!res.ok) return null;
      return (await res.json()) as LiveQuotesResponse;
    } finally {
      clearTimeout(timeout);
    }
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

/**
 * Combined fertilizer+cement live quotes (GET /market/live/all) -- meant to be called
 * client-side via useLiveQuotes(), not awaited during SSR. This is the same up-to-35s,
 * no-SLA psxdata scrape as fetchLiveQuotes()/fetchCementLiveQuotes(); the point of this
 * one is where it's called from, not what it does.
 */
export async function fetchLiveQuotesAll(): Promise<LiveQuotesResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/market/live/all`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as LiveQuotesResponse;
  } catch {
    return null;
  }
}

export interface SingleLiveQuoteResponse {
  data_source: string;
  disclaimer: string;
  fetched_at: string;
  quote: LiveQuote;
}

/** Single-symbol live quote (GET /market/quote/{symbol}) -- meant to be called client-side
 * via useLiveQuote(), so a company page's own render never waits on this scrape. */
export async function fetchSingleLiveQuote(symbol: string): Promise<SingleLiveQuoteResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/market/quote/${encodeURIComponent(symbol)}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as SingleLiveQuoteResponse;
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

export interface EquityResearchSection {
  title: string;
  content: string;
  has_real_content: boolean;
  missing_evidence: string[];
}

export interface EquityResearchReportResponse {
  ticker: string;
  not_covered: boolean;
  unavailable: boolean;
  error?: string;
  coverage_note?: string;
  company_name?: string;
  status?: string;
  is_preliminary?: boolean;
  published_at?: string | null;
  sections_total?: number;
  sections_with_real_content?: number;
  sections?: EquityResearchSection[];
}

// Real, citation-grounded report from Equity-research's 8-agent pipeline -- see
// backend/app/api/equity_research.py. Deliberately not an LLM call from the frontend:
// this relays whatever the real pipeline actually published, including its gaps.
export async function fetchEquityResearchReport(ticker: string): Promise<EquityResearchReportResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/equity-research/${encodeURIComponent(ticker)}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as EquityResearchReportResponse;
  } catch {
    return null;
  }
}

// ─── Analyst Agent types ─────────────────────────────────────────────────────

export interface ForensicFlag {
  flag_code: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "clear" | "watch" | "triggered" | "not_applicable" | "insufficient_data";
  periods: string[];
  observed_value: string | null;
  sector_reference: string | null;
  explanation: string;
  possible_benign_explanations: string[];
  confidence: string;
}

export interface DuPontRow {
  period_end: string;
  net_margin: number | null;
  asset_turnover: number | null;
  equity_multiplier: number | null;
  roe_3way: number | null;
  roe_reported: number | null;
  ebit_margin: number | null;
  interest_burden: number | null;
  tax_burden: number | null;
}

export interface ForensicsData {
  issuer_id: number;
  symbol: string;
  as_of: string;
  sub_scores: {
    operating_health: number | null;
    earnings_quality: number | null;
    balance_sheet: number | null;
    capital_allocation: number | null;
    governance: number | null;
  };
  business_health: string;
  health_confidence: string;
  dupont: DuPontRow[];
  cash_conversion: { period_end: string; profit_after_tax: number; operating_cash_flow: number | null; cfo_pat_ratio: number | null }[];
  interest_coverage: { period_end: string; ebit_proxy: number | null; finance_cost: number | null; coverage: number | null }[];
  leverage: { period_end: string; debt_to_equity: number | null; debt_to_assets: number | null; current_ratio: number | null }[];
  flags: ForensicFlag[];
  missing_data_items: string[];
  data_coverage_pct: number;
  is_research_only: true;
  disclaimer: string;
}

export interface CAPMDiagnosticsData {
  issuer_id: number;
  symbol: string;
  benchmark: string;
  window_label: string;
  n_obs: number;
  beta: number | null;
  alpha_annualised: number | null;
  r_squared: number | null;
  residual_vol_annualised: number | null;
  beta_t_stat: number | null;
  beta_p_value: number | null;
  beta_ci_low: number | null;
  beta_ci_high: number | null;
  up_market_beta: number | null;
  down_market_beta: number | null;
  asymmetry_note: string | null;
  zero_return_pct: number | null;
  stale_price_warning: boolean;
  required_return_pct: number | null;
  required_return_low_pct: number | null;
  required_return_high_pct: number | null;
  risk_free_rate_pct: number | null;
  erp_pct: number | null;
  rolling_beta: { window_end: string; beta: number; n_obs: number }[];
  confidence: string;
  confidence_notes: string[];
  is_research_only?: true;
  disclaimer?: string;
}

export interface FactorExposure {
  factor_name: string;
  beta: number | null;
  beta_se: number | null;
  t_stat: number | null;
  p_value: number | null;
  ci_low: number | null;
  ci_high: number | null;
  interpretation: string;
  data_available: boolean;
}

export interface AnalystRunResult {
  status: string;
  run_id?: number;
  message?: string;
  symbol?: string;
  created_at?: string;
  completed_at?: string;
  error_message?: string | null;
  packet?: {
    research_posture: string;
    business_health: string;
    confidence: string;
    one_sentence_view: string | null;
    decision_hinge: string | null;
    is_approved: boolean;
    packet_json: Record<string, unknown>;
  } | null;
  is_research_only?: true;
  disclaimer?: string;
}

export async function fetchAnalystRun(issuerId: number): Promise<AnalystRunResult | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies/${issuerId}/analyst-run/latest`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as AnalystRunResult;
  } catch {
    return null;
  }
}

export async function triggerAnalystRun(issuerId: number): Promise<AnalystRunResult | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies/${issuerId}/analyst-run`, {
      method: "POST",
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as AnalystRunResult;
  } catch {
    return null;
  }
}

export async function fetchForensics(issuerId: number): Promise<ForensicsData | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies/${issuerId}/forensics`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as ForensicsData;
  } catch {
    return null;
  }
}

export async function fetchCAPMDiagnostics(issuerId: number): Promise<CAPMDiagnosticsData | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/companies/${issuerId}/capm-diagnostics`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as CAPMDiagnosticsData;
  } catch {
    return null;
  }
}

// ─── ML signal engine types (walk-forward-validated calibrated classifier) ──────────────────

export interface MlSignalResearch {
  is_research_only: true;
  signal: string;
  disclaimer?: string;
  reason?: string;
  as_of_date?: string;
  model_version?: number;
  outperformance_probability: number | null;
  validation_observations: number | null;
  validation_accuracy: number | null;
  validation_buy_precision: number | null;
  validation_sell_precision: number | null;
  validation_brier_score: number | null;
  validation_roc_auc: number | null;
  is_public?: boolean;
}

export async function fetchMlSignalResearch(issuerId: number): Promise<MlSignalResearch | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/ml-signals/research/${issuerId}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as MlSignalResearch;
  } catch {
    return null;
  }
}

// ─── Kronos quant forecast + Signal Qualification Gate ──────────────────────────

export interface SignalQualificationTrackRecord {
  n_observations: number;
  hits: number;
  accuracy: number;
  p_value_vs_random: number;
  significant_at_10pct: boolean;
}

export interface SignalQualification {
  signal: "BUY" | "SELL" | "HOLD" | "NO_SIGNAL";
  qualified: boolean;
  reason: string;
  track_record: SignalQualificationTrackRecord | null;
}

export interface QuantForecast {
  ok: boolean;
  reason?: string;
  ticker?: string;
  issuer_name?: string;
  as_of_date?: string;
  last_real_close?: number;
  horizon_days?: number;
  model_source?: string;
  n_samples?: number;
  p_positive_return?: number;
  expected_return_pct?: number;
  downside_var_pct?: number;
  expected_volatility_pct?: number;
  trend_regime?: "bullish" | "bearish" | "neutral";
  model_confidence?: "medium-high" | "medium" | "low";
  signal_qualification?: SignalQualification;
}

// Real Kronos ensemble forecast, on-demand only (costs ~5-30s, a genuine 15-sample
// CPU inference run) -- never bundled into the company page's eager parallel fetch.
export async function fetchQuantForecast(ticker: string, horizonDays = 5): Promise<QuantForecast | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/quant-forecast/${encodeURIComponent(ticker)}?horizon_days=${horizonDays}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as QuantForecast;
  } catch {
    return null;
  }
}

export interface MlModelEvidence {
  is_research_only: true;
  reason?: string;
  disclaimer?: string;
  as_of_date?: string;
  calculated_at?: string;
  model_version?: number;
  observations: number | null;
  accuracy: number | null;
  buy_precision: number | null;
  sell_precision: number | null;
  brier_score: number | null;
  roc_auc: number | null;
}

export async function fetchMlModelEvidence(): Promise<MlModelEvidence | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/ml-signals/research/evidence`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as MlModelEvidence;
  } catch {
    return null;
  }
}
