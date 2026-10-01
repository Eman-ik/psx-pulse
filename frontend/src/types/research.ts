export interface EquityResearchReportResponse {
  ticker: string;
  company_name: string;
  not_covered?: boolean;
  unavailable?: boolean;
  coverage_note?: string;
  published_at?: string;
  sections_total?: number;
  sections_with_real_content?: number;
  sections?: ResearchSection[];
}

export interface ResearchSection {
  title: string;
  content: string;
  has_real_content: boolean;
  missing_evidence?: string[];
}

export interface Workspace {
  ticker: string;
  generated_at: string;
  coverage_tier: 'full' | 'unverified' | 'price_only';
  evidence: {
    source_count: number;
    announcement_count: number;
    financial_series_count: number;
    ratio_series_count: number;
    fundamentals_renderable: boolean;
  };
  overview: {
    issuer: {
      name: string;
      short_name: string | null;
      sector_name: string;
      business_description: string | null;
      website: string | null;
      auditor: string | null;
      fiscal_year_end_month: number | null;
      establishment_year: number | null;
    };
    data_delay_notice: string;
    symbol: string;
    security_id: number | null;
    free_float_pct: number | null;
    financials: Record<string, Point[]>;
    ratios: Record<string, Ratio>;
    payouts: Payout[];
    announcements: Announcement[];
    sources: Source[];
    operational_metrics: Record<string, Point[]>;
    thesis: Thesis | null;
  };
  peers: Peer[];
  industry: IndustryIntelligence;
}

export interface Point {
  period_end: string;
  value: number;
  unit?: string;
  period_type?: string;
}

export interface Ratio {
  name: string;
  category: string;
  unit: string;
  formula: string;
  values: Point[];
}

export interface Payout {
  action_type: string;
  effective_date: string;
  ratio_or_amount: number | null;
}

export interface Announcement {
  id: number;
  title: string;
  category: string;
  published_at: string;
  summary: string | null;
  source_url: string | null;
}

export interface Source {
  document_type: string;
  source_tier: string;
  url: string | null;
  fetched_at: string;
}

export interface Thesis {
  as_of_date: string;
  bull_case: string;
  base_case: string;
  bear_case: string;
  key_catalysts: string[];
  key_risks: string[];
}

export interface Peer {
  id: number;
  symbol: string;
  name: string;
  sector: string;
  market_cap: number | null;
  eps: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  net_profit_margin: number | null;
  coverage_status: string;
}

export interface IndustryIntelligence {
  sector: string;
  industry_avg_roe?: number;
  industry_avg_debt_equity?: number;
  industry_growth_rate?: number;
  competitive_position?: string;
  market_share?: number;
  key_competitors?: string[];
  industry_trends?: string[];
}
