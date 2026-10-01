/**
 * Sprint 4: Company Detail Page
 *
 * Main company view with financials and context.
 */
'use client';

import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { FinancialTable } from '@/components/FinancialTable';

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
        const res = await fetch(`http://localhost:8000/companies/${ticker}`);
        if (!res.ok) throw new Error('Company not found');
        const data = await res.json();
        setCompany(data);

        // Fetch periods
        const periodsRes = await fetch(`http://localhost:8000/companies/${data.id}/periods`);
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
        const res = await fetch(`http://localhost:8000/periods/${selectedPeriodId}/facts`);
        const factsData = await res.json();
        setFacts(factsData);

        // Fetch sources for all facts
        const sourcesMap: { [key: number]: Source } = {};
        for (const fact of factsData) {
          if (!sourcesMap[fact.source_id]) {
            const sourceRes = await fetch(`http://localhost:8000/sources/${fact.source_id}`);
            const sourceData = await sourceRes.json();
            sourcesMap[fact.source_id] = sourceData;
          }
        }
        setSources(sourcesMap);

        // Fetch prior period facts if available
        const periodRes = await fetch(`http://localhost:8000/periods/${selectedPeriodId}`);
        const period = await periodRes.json();

        if (period.period_type === 'annual' && period.fiscal_year > 1) {
          const priorYearRes = await fetch(
            `http://localhost:8000/companies/${company?.id}/periods?fiscal_year=${period.fiscal_year - 1}&period_type=annual`
          );
          const priorPeriods = await priorYearRes.json();
          if (priorPeriods.length > 0) {
            const priorFactsRes = await fetch(`http://localhost:8000/periods/${priorPeriods[0].id}/facts`);
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
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="text-center py-12">
            <div className="text-gray-600">Loading company data...</div>
          </div>
        </div>
      </main>
    );
  }

  if (error || !company) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="text-center py-12">
            <div className="text-red-600 font-semibold">{error || 'Company not found'}</div>
          </div>
        </div>
      </main>
    );
  }

  const getCoverageBadgeColor = (tier: string) => {
    switch (tier) {
      case 'full': return 'bg-green-100 text-green-800';
      case 'partial': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl font-bold mb-2">{company.ticker}</h1>
              <p className="text-lg text-gray-600 mb-3">{company.name}</p>
              <div className="flex gap-3">
                <span className="text-sm text-gray-600">Sector: {company.sector}</span>
                <span className={`text-xs px-2 py-1 rounded ${getCoverageBadgeColor(company.coverage_tier)}`}>
                  {company.coverage_tier.toUpperCase()} COVERAGE
                </span>
              </div>
            </div>
            <a
              href="/search"
              className="text-blue-600 hover:text-blue-800 underline text-sm"
            >
              ← Back to Search
            </a>
          </div>
        </div>
      </div>

      {/* Period Selector */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex gap-2 overflow-x-auto pb-2">
            {periods.map(period => (
              <button
                key={period.id}
                onClick={() => setSelectedPeriodId(period.id)}
                className={`px-4 py-2 rounded whitespace-nowrap transition ${
                  selectedPeriodId === period.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
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
      <div className="max-w-6xl mx-auto px-6 py-8">
        {facts.length === 0 ? (
          <div className="bg-white rounded-lg p-8 text-center">
            <p className="text-gray-600">No financial data available for this period</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-8">
            <FinancialTable
              facts={facts}
              sources={sources}
              priorFacts={priorFacts}
            />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-800 text-gray-300 py-8 mt-16">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-sm">
            Khronos Financial Research MVP • Sprint 4 Frontend
          </p>
        </div>
      </div>
    </main>
  );
}
