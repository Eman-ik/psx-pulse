'use client';

import { useState } from 'react';
import { Search, TrendingUp, TrendingDown, AlertCircle, CheckCircle2 } from 'lucide-react';
import { API_BASE_URL } from '@/lib/config';
import Link from 'next/link';

interface CompanyMetrics {
  ticker: string;
  name: string;
  sector: string;
  price: number;
  currency: string;
  // Financial metrics
  revenue: number | null;
  eps: number | null;
  net_margin: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  dividend_yield: number | null;
  // Valuation metrics
  pe_ratio: number | null;
  pb_ratio: number | null;
  // Technical metrics
  rsi: number | null;
  price_vs_200dma: number | null;
  // Research
  confidence_score: number;
  financial_health: string;
  valuation_assessment: string;
  risk_level: number;
}

const MISSING = '—';

function MetricValue({ value, format = 'number' }: { value: number | null; format?: 'number' | 'pct' | 'ratio' }) {
  if (value === null) return <span className="text-muted">{MISSING}</span>;

  if (format === 'pct') {
    return <span className={value >= 0 ? 'text-positive' : 'text-negative'}>{value > 0 ? '+' : ''}{value.toFixed(1)}%</span>;
  }
  if (format === 'ratio') {
    return <span className="text-foreground">{value.toFixed(2)}x</span>;
  }
  return <span className="text-foreground">{value.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>;
}

function ComparisonTable({ left, right }: { left: CompanyMetrics; right: CompanyMetrics }) {
  const metrics = [
    { label: 'Price', key: 'price', format: 'number', subtext: 'PKR' },
    { section: 'Financial Performance' },
    { label: 'Annual Revenue', key: 'revenue', format: 'number', subtext: 'PKR bn' },
    { label: 'EPS (TTM)', key: 'eps', format: 'number', subtext: 'PKR' },
    { label: 'Net Margin', key: 'net_margin', format: 'pct' },
    { label: 'ROE', key: 'roe', format: 'pct' },
    { label: 'Debt/Equity', key: 'debt_to_equity', format: 'ratio' },
    { label: 'Dividend Yield', key: 'dividend_yield', format: 'pct' },
    { section: 'Valuation' },
    { label: 'P/E Ratio', key: 'pe_ratio', format: 'ratio' },
    { label: 'P/B Ratio', key: 'pb_ratio', format: 'ratio' },
    { section: 'Technical' },
    { label: 'RSI (14)', key: 'rsi', format: 'number' },
    { label: 'Price vs 200 DMA', key: 'price_vs_200dma', format: 'pct' },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted">Metric</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-foreground">{left.ticker}</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-foreground">{right.ticker}</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric, i) => {
            if ('section' in metric) {
              return (
                <tr key={`section-${i}`} className="border-t border-border/50">
                  <td colSpan={3} className="px-4 py-3 text-xs font-bold text-muted uppercase">{metric.section}</td>
                </tr>
              );
            }

            const value_l = left[metric.key as keyof CompanyMetrics] as number | null;
            const value_r = right[metric.key as keyof CompanyMetrics] as number | null;

            return (
              <tr key={metric.key} className="border-b border-border/30 hover:bg-surface/50">
                <td className="px-4 py-3 text-muted">
                  {metric.label}
                  {metric.subtext && <span className="ml-1 text-xs text-muted">({metric.subtext})</span>}
                </td>
                <td className="px-4 py-3 text-right">
                  <MetricValue value={value_l} format={metric.format as 'number' | 'pct' | 'ratio'} />
                </td>
                <td className="px-4 py-3 text-right">
                  <MetricValue value={value_r} format={metric.format as 'number' | 'pct' | 'ratio'} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RiskAssessment({ ticker, risk_level }: { ticker: string; risk_level: number }) {
  const riskColor = risk_level >= 7 ? 'text-negative' : risk_level >= 4 ? 'text-accent' : 'text-positive';
  const riskLabel = risk_level >= 7 ? 'High' : risk_level >= 4 ? 'Medium' : 'Low';

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-muted uppercase">Risk Level</p>
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
          <div
            className={`h-full transition ${risk_level >= 7 ? 'bg-negative' : risk_level >= 4 ? 'bg-accent' : 'bg-positive'}`}
            style={{ width: `${(risk_level / 10) * 100}%` }}
          />
        </div>
        <span className={`text-sm font-semibold ${riskColor}`}>{riskLabel}</span>
      </div>
    </div>
  );
}

function CompanyCard({ metrics, position = 'left' }: { metrics: CompanyMetrics; position?: 'left' | 'right' }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-6 space-y-6">
      <div>
        <p className="text-sm text-muted">Company</p>
        <p className="text-2xl font-bold text-foreground">{metrics.ticker}</p>
        <p className="text-xs text-muted">{metrics.name}</p>
        <p className="text-xs text-muted mt-1">{metrics.sector}</p>
      </div>

      <div className="pt-4 border-t border-border">
        <p className="text-sm text-muted mb-2">Current Price</p>
        <p className="text-3xl font-bold text-foreground">PKR {metrics.price?.toFixed(2)}</p>
      </div>

      <RiskAssessment ticker={metrics.ticker} risk_level={metrics.risk_level} />

      <div className="pt-4 border-t border-border space-y-3">
        <div>
          <p className="text-xs text-muted uppercase">Financial Health</p>
          <p className="text-sm font-semibold text-foreground mt-1">{metrics.financial_health || 'Not assessed'}</p>
        </div>
        <div>
          <p className="text-xs text-muted uppercase">Valuation</p>
          <p className="text-sm font-semibold text-foreground mt-1">{metrics.valuation_assessment || 'Not assessed'}</p>
        </div>
      </div>

      <div className="pt-4 border-t border-border">
        <p className="text-xs text-muted">Data Confidence</p>
        <div className="flex items-center gap-2 mt-2">
          <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
            <div className="h-full bg-accent" style={{ width: `${metrics.confidence_score}%` }} />
          </div>
          <span className="text-xs font-semibold text-foreground">{Math.round(metrics.confidence_score)}%</span>
        </div>
      </div>

      <Link href={`/research?t=${metrics.ticker}`} className="w-full block text-center px-4 py-2.5 rounded-lg border border-accent/30 hover:border-accent/60 text-accent font-medium text-sm transition-colors">
        Full Research →
      </Link>
    </div>
  );
}

export default function CompareCompanies() {
  const [leftTicker, setLeftTicker] = useState('FFC');
  const [rightTicker, setRightTicker] = useState('EFERT');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [leftData, setLeftData] = useState<CompanyMetrics | null>(null);
  const [rightData, setRightData] = useState<CompanyMetrics | null>(null);

  const handleCompare = async () => {
    if (!leftTicker.trim() || !rightTicker.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const [leftRes, rightRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/companies/${leftTicker.toUpperCase()}/overview`),
        fetch(`${API_BASE_URL}/api/v1/companies/${rightTicker.toUpperCase()}/overview`),
      ]);

      if (!leftRes.ok || !rightRes.ok) {
        throw new Error('One or both companies not found');
      }

      const [left, right] = await Promise.all([leftRes.json(), rightRes.json()]);

      // Get research data for both
      const [leftAnalysisRes, rightAnalysisRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/research/${leftTicker.toUpperCase()}/analysis`),
        fetch(`${API_BASE_URL}/api/v1/research/${rightTicker.toUpperCase()}/analysis`),
      ]);

      const leftAnalysis = leftAnalysisRes.ok ? await leftAnalysisRes.json() : {};
      const rightAnalysis = rightAnalysisRes.ok ? await rightAnalysisRes.json() : {};

      const mapCompany = (company: any, analysis: any) => ({
        ticker: company.symbol,
        name: company.name,
        sector: company.sector,
        price: company.price?.close || null,
        currency: 'PKR',
        revenue: null,
        eps: null,
        net_margin: null,
        roe: null,
        debt_to_equity: null,
        dividend_yield: null,
        pe_ratio: null,
        pb_ratio: null,
        rsi: null,
        price_vs_200dma: null,
        confidence_score: company.research_overview?.data_availability || 0,
        financial_health: company.research_overview?.business_health || 'Not assessed',
        valuation_assessment: company.research_overview?.valuation || 'Not assessed',
        risk_level: company.research_overview?.risk_level === 'Medium' ? 5 : company.research_overview?.risk_level === 'High' ? 7 : 3,
      });

      setLeftData(mapCompany(left, leftAnalysis));
      setRightData(mapCompany(right, rightAnalysis));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to compare');
      setLeftData(null);
      setRightData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto max-w-7xl px-6 py-8 sm:px-8">
          <h1 className="text-4xl font-bold mb-2">Compare Companies</h1>
          <p className="text-sm text-muted">Side-by-side financial, valuation, and technical analysis</p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8 sm:px-8">
        {/* Input Section */}
        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted block mb-2">
              First Company
            </label>
            <input
              type="text"
              value={leftTicker}
              onChange={(e) => setLeftTicker(e.target.value.toUpperCase())}
              placeholder="FFC"
              className="glass-input w-full text-sm"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleCompare}
              disabled={loading}
              className="w-full px-4 py-2.5 rounded-lg font-medium text-sm transition-all bg-accent/20 border border-accent/40 text-foreground hover:bg-accent/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Comparing...' : 'Compare'}
            </button>
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted block mb-2">
              Second Company
            </label>
            <input
              type="text"
              value={rightTicker}
              onChange={(e) => setRightTicker(e.target.value.toUpperCase())}
              placeholder="EFERT"
              className="glass-input w-full text-sm"
            />
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-lg border border-negative/30 bg-negative/5 p-4 flex gap-3">
            <AlertCircle className="h-4 w-4 text-negative shrink-0 mt-0.5" />
            <p className="text-sm text-negative">{error}</p>
          </div>
        )}

        {/* Comparison View */}
        {leftData && rightData && (
          <div className="space-y-8">
            {/* Cards View */}
            <div className="grid gap-6 lg:grid-cols-2">
              <CompanyCard metrics={leftData} position="left" />
              <CompanyCard metrics={rightData} position="right" />
            </div>

            {/* Metrics Table */}
            <div className="rounded-lg border border-border bg-surface p-6">
              <h2 className="text-lg font-bold mb-4">Metrics Comparison</h2>
              <ComparisonTable left={leftData} right={rightData} />
              <p className="text-xs text-muted mt-4">
                All figures sourced from real backend data. Missing data shows as "—" with no synthesis.
              </p>
            </div>

            {/* Investment Thesis */}
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-lg border border-border/50 bg-surface/50 p-6">
                <h3 className="text-base font-bold mb-4">Key Strengths</h3>
                <div className="space-y-3 text-sm text-muted">
                  <div className="flex gap-2">
                    <CheckCircle2 className="h-4 w-4 text-positive shrink-0 mt-0.5" />
                    <p>{leftData.financial_health}</p>
                  </div>
                  <div className="flex gap-2">
                    <CheckCircle2 className="h-4 w-4 text-positive shrink-0 mt-0.5" />
                    <p>{leftData.valuation_assessment}</p>
                  </div>
                  <p className="text-xs text-muted mt-2 italic">Research-backed assessment from institutional engines</p>
                </div>
              </div>

              <div className="rounded-lg border border-border/50 bg-surface/50 p-6">
                <h3 className="text-base font-bold mb-4">Key Considerations</h3>
                <div className="space-y-3 text-sm text-muted">
                  <div className="flex gap-2">
                    <AlertCircle className="h-4 w-4 text-negative shrink-0 mt-0.5" />
                    <p>{rightData.financial_health}</p>
                  </div>
                  <div className="flex gap-2">
                    <AlertCircle className="h-4 w-4 text-negative shrink-0 mt-0.5" />
                    <p>{rightData.valuation_assessment}</p>
                  </div>
                  <p className="text-xs text-muted mt-2 italic">Detailed risk analysis at full research pages</p>
                </div>
              </div>
            </div>

            {/* Deep Dive Links */}
            <div className="rounded-lg border border-border/50 bg-surface/50 p-6">
              <h3 className="text-base font-bold mb-4">Explore Further</h3>
              <p className="text-sm text-muted mb-4">
                This comparison shows side-by-side snapshots. Use the links below for complete institutional analysis, peer benchmarking, historical valuation, governance, and scorecard analysis.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                {[leftData, rightData].map((company) => (
                  <div key={company.ticker} className="space-y-2">
                    <p className="text-xs font-semibold text-muted uppercase">{company.ticker}</p>
                    <div className="flex flex-wrap gap-2">
                      <Link href={`/research?t=${company.ticker}&tab=overview`} className="px-3 py-1.5 rounded text-xs border border-border hover:border-foreground/50 text-muted hover:text-foreground transition-colors">
                        Overview
                      </Link>
                      <Link href={`/research?t=${company.ticker}&tab=financials`} className="px-3 py-1.5 rounded text-xs border border-border hover:border-foreground/50 text-muted hover:text-foreground transition-colors">
                        Financials
                      </Link>
                      <Link href={`/research?t=${company.ticker}&tab=valuation`} className="px-3 py-1.5 rounded text-xs border border-border hover:border-foreground/50 text-muted hover:text-foreground transition-colors">
                        Valuation
                      </Link>
                      <Link href={`/research?t=${company.ticker}&tab=technical`} className="px-3 py-1.5 rounded text-xs border border-border hover:border-foreground/50 text-muted hover:text-foreground transition-colors">
                        Technical
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {!leftData && !rightData && !error && (
          <div className="rounded-lg border border-border/50 bg-surface/50 p-12 text-center">
            <p className="text-muted">Enter two PSX tickers above and press Compare to see side-by-side analysis.</p>
            <p className="text-xs text-muted mt-2">Example: FFC vs EFERT</p>
          </div>
        )}
      </main>
    </div>
  );
}
