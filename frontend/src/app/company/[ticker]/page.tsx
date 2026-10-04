/**
 * Sprint 4: Company Detail Page
 *
 * Main company view with financials and context.
 */
'use client';

import { API_BASE_URL } from "@/lib/config";
import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { FinancialTable } from '@/components/FinancialTable';
import { SectionHeader, LoadingCard, ErrorState, StatusBadge } from '@/components/glass';

interface Company {
  id: number;
  ticker: string;
  name: string;
  sector: string;
  coverage_tier: string;
}

interface Period {
  id: number;
  period_type: string;
  fiscal_year: number;
  quarter?: number;
}

interface FinancialFact {
  id: number;
  metric: string;
  value: number;
  unit: string;
  statement_type: string;
  source_id: number;
  source_page?: number;
  validation_status: string;
}

interface Source {
  id: number;
  title: string;
  document_date?: string;
  url?: string;
}

export default function CompanyPage() {
  const params = useParams();
  const ticker = params.ticker as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [periods, setPeriods] = useState<Period[]>([]);
  const [selectedPeriodId, setSelectedPeriodId] = useState<number | null>(null);
  const [facts, setFacts] = useState<FinancialFact[]>([]);
  const [sources, setSources] = useState<{ [key: number]: Source }>({});
  const [priorFacts, setPriorFacts] = useState<{ [key: string]: FinancialFact }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch company data
  useEffect(() => {
    if (!ticker) return;

    const fetchCompany = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/companies/${ticker}`);
        if (!res.ok) throw new Error('Company not found');
        const data = await res.json();
        setCompany(data);

        // Fetch periods
        const periodsRes = await fetch(`${API_BASE_URL}/companies/${data.id}/periods`);
        const periodsData = await periodsRes.json();
        setPeriods(periodsData);

        // Set most recent period as selected
        if (periodsData.length > 0) {
          const sorted = [...periodsData].sort((a, b) => {
            if (a.fiscal_year !== b.fiscal_year) return b.fiscal_year - a.fiscal_year;
            if (a.period_type !== b.period_type) return a.period_type === 'annual' ? -1 : 1;
            return (b.quarter || 0) - (a.quarter || 0);
          });
          setSelectedPeriodId(sorted[0].id);
        }

        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load company');
        setLoading(false);
      }
    };

    fetchCompany();
  }, [ticker]);

  // Fetch facts when period selected
  useEffect(() => {
    if (!selectedPeriodId) return;

    const fetchFacts = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/periods/${selectedPeriodId}/facts`);
        const factsData = await res.json();
        setFacts(factsData);

        // Fetch sources for all facts
        const sourcesMap: { [key: number]: Source } = {};
        for (const fact of factsData) {
          if (!sourcesMap[fact.source_id]) {
            const sourceRes = await fetch(`${API_BASE_URL}/sources/${fact.source_id}`);
            const sourceData = await sourceRes.json();
            sourcesMap[fact.source_id] = sourceData;
          }
        }
        setSources(sourcesMap);

        // Fetch prior period facts if available
        const periodRes = await fetch(`${API_BASE_URL}/periods/${selectedPeriodId}`);
        const period = await periodRes.json();

        if (period.period_type === 'annual' && period.fiscal_year > 1) {
          const priorYearRes = await fetch(
            `${API_BASE_URL}/companies/${company?.id}/periods?fiscal_year=${period.fiscal_year - 1}&period_type=annual`
          );
          const priorPeriods = await priorYearRes.json();
          if (priorPeriods.length > 0) {
            const priorFactsRes = await fetch(`${API_BASE_URL}/periods/${priorPeriods[0].id}/facts`);
            const priorFactsData = await priorFactsRes.json();
            const priorFactsMap: { [key: string]: FinancialFact } = {};
            for (const fact of priorFactsData) {
              priorFactsMap[fact.metric] = fact;
            }
            setPriorFacts(priorFactsMap);
          }
        }
      } catch (err) {
        console.error('Failed to fetch facts:', err);
      }
    };

    fetchFacts();
  }, [selectedPeriodId, company?.id]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[var(--bg-page-deep)]">
        <div className="atmospheric-bg" aria-hidden="true" />
        <div className="grain-overlay" aria-hidden="true" />
        <div className="relative z-10 max-w-6xl mx-auto px-6 py-12">
          <LoadingCard message="Loading company data..." />
        </div>
      </main>
    );
  }

  if (error || !company) {
    return (
      <main className="min-h-screen bg-[var(--bg-page-deep)]">
        <div className="atmospheric-bg" aria-hidden="true" />
        <div className="grain-overlay" aria-hidden="true" />
        <div className="relative z-10 max-w-6xl mx-auto px-6 py-12">
          <ErrorState
            title="Company Not Found"
            description={error || 'The company you are looking for does not exist in our database.'}
            action={<a href="/search" className="glass-btn-secondary text-sm">← Back to Search</a>}
          />
        </div>
      </main>
    );
  }

  const getCoverageBadgeStatus = (tier: string): 'positive' | 'warning' | 'neutral' => {
    switch (tier) {
      case 'full': return 'positive';
      case 'partial': return 'warning';
      default: return 'neutral';
    }
  };

  return (
    <main className="min-h-screen bg-[var(--bg-page-deep)]">
      <div className="atmospheric-bg" aria-hidden="true" />
      <div className="grain-overlay" aria-hidden="true" />

      <div className="relative z-10">
        {/* Header */}
        <div className="border-b border-[rgba(142,156,183,0.2)]">
          <div className="max-w-6xl mx-auto px-6 py-12">
            <div className="flex justify-between items-start gap-8">
              <div className="flex-1">
                <h1 className="text-5xl font-bold mb-2 text-[var(--text-primary)]">{company.ticker}</h1>
                <p className="text-lg text-[var(--text-secondary)] mb-4">{company.name}</p>
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-sm text-[var(--text-secondary)]">Sector: {company.sector}</span>
                  <StatusBadge
                    status={getCoverageBadgeStatus(company.coverage_tier)}
                    label={`${company.coverage_tier.toUpperCase()} Coverage`}
                  />
                </div>
              </div>
              <a
                href="/search"
                className="glass-btn-secondary text-sm whitespace-nowrap"
              >
                ← Back to Search
              </a>
            </div>
          </div>
        </div>

        {/* Period Selector */}
        <div className="border-b border-[rgba(142,156,183,0.2)] sticky top-0 z-10 bg-[var(--surface-glass)]">
          <div className="max-w-6xl mx-auto px-6 py-4">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {periods.map(period => (
                <button
                  key={period.id}
                  onClick={() => setSelectedPeriodId(period.id)}
                  className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
                    selectedPeriodId === period.id
                      ? 'glass-btn-primary text-xs font-semibold'
                      : 'glass-btn-secondary text-xs font-semibold'
                  }`}
                >
                  {period.period_type === 'annual'
                    ? `FY${period.fiscal_year}`
                    : `Q${period.quarter} ${period.fiscal_year}`}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Financial Data */}
        <div className="max-w-6xl mx-auto px-6 py-12">
          {facts.length === 0 ? (
            <div className="glass-card p-8 text-center">
              <p className="text-[var(--text-secondary)]">No financial data available for this period</p>
            </div>
          ) : (
            <div className="glass-strong p-8">
              <FinancialTable
                facts={facts}
                sources={sources}
                priorFacts={priorFacts}
              />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
