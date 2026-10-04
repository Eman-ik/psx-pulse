'use client';

import { useState } from 'react';
import { ChevronDown, AlertCircle, TrendingUp, TrendingDown, CheckCircle2, XCircle, Link as LinkIcon } from 'lucide-react';
import { API_BASE_URL } from '@/lib/config';
import Link from 'next/link';

interface ResearchAnalysis {
  ticker?: string;
  confidence_score?: number;
  business_health?: { assessment?: string; narrative?: string; strengths?: string[] };
  what_changed?: { narrative?: string };
  earnings_quality?: { assessment?: string };
  bull_bear_case?: { bull_case?: { thesis?: string }; bear_case?: { thesis?: string }; critical_debate?: string };
  red_flags?: { flags?: Array<{ issue?: string }> };
  risk_engine?: { summary?: { high?: number; medium?: number }; all_risks?: Array<{ title?: string }> };
  catalyst_engine?: { catalysts?: Array<{ title?: string }> };
  valuation_context?: { assessment?: string; narrative?: string };
  what_to_watch?: { watch_metrics?: Array<{ metric?: string }> };
}

const SUGGESTED_QUESTIONS = [
  'Is this company fundamentally strong?',
  'What changed in the latest quarter?',
  'What are the biggest risks?',
  'What is the valuation like?',
  'What are the bull and bear cases?',
  'What would change my view?',
];

const QUESTION_ROUTING: Record<string, string[]> = {
  fundamental: ['fundamentally', 'strong', 'health', 'business'],
  changes: ['changed', 'quarter', 'period', 'latest', 'recent'],
  risks: ['risks', 'biggest', 'problems', 'concerns', 'dangers'],
  valuation: ['valuation', 'expensive', 'cheap', 'price', 'pe', 'fair', 'attractive'],
  bull_bear: ['bull', 'bear', 'case', 'thesis', 'upside', 'downside'],
  catalysts: ['catalyst', 'events', 'trigger', 'upcoming', 'news'],
  earnings: ['earnings', 'profit', 'quality', 'revenue'],
};

function classifyQuestion(q: string): string {
  const lower = q.toLowerCase();
  for (const [category, keywords] of Object.entries(QUESTION_ROUTING)) {
    if (keywords.some(kw => lower.includes(kw))) {
      return category;
    }
  }
  return 'general';
}

export default function AskPanel() {
  const [ticker, setTicker] = useState('FFC');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResearchAnalysis | null>(null);
  const [showRawEvidence, setShowRawEvidence] = useState(false);
  const [askedQuestion, setAskedQuestion] = useState('');

  const handleAnalyze = async (q: string = '') => {
    const finalQuestion = q || question;
    if (!finalQuestion.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/research/${ticker.toUpperCase()}/analysis`,
        { method: 'GET', headers: { 'Content-Type': 'application/json' } }
      );

      if (!response.ok) {
        throw new Error(`${response.status === 404 ? 'Company not found' : 'Analysis unavailable'}`);
      }

      const data = await response.json();
      setResult(data);
      setAskedQuestion(finalQuestion);
      setQuestion('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to analyze');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (q: string) => {
    setQuestion('');
    handleAnalyze(q);
  };

  return (
    <div className="min-h-screen bg-transparent text-[var(--text-primary)]">
      <header className="border-b border-[rgba(142,156,183,0.2)]">
        <div className="mx-auto max-w-4xl px-6 pt-8 sm:px-8 pb-8">
          <h1 className="text-4xl font-bold mb-2">Ask PSX Pulse</h1>
          <p className="text-sm text-[var(--text-secondary)]">Source-backed equity research for PSX companies</p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
        {/* Company Selector */}
        <div className="mb-8">
          <label className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] mb-2 block">
            Company
          </label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="FFC, EFERT, PSX..."
            className="glass-input w-full text-sm"
          />
        </div>

        {/* Question Input */}
        <div className="mb-6 space-y-3">
          <label className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] block">
            Your Question
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && e.ctrlKey && handleAnalyze()}
            placeholder="Ask about fundamentals, risks, valuation, changes, catalysts..."
            className="glass-input w-full text-sm min-h-16 resize-none"
          />
          <button
            onClick={() => handleAnalyze()}
            disabled={loading || !ticker.trim()}
            className="w-full px-4 py-2.5 rounded-lg font-medium text-sm transition-all bg-[rgba(29,185,84,0.2)] border border-[rgba(29,185,84,0.4)] text-[var(--text-primary)] hover:bg-[rgba(29,185,84,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Researching...' : '→ Research'}
          </button>
        </div>

        {/* Suggested Questions */}
        {!result && !error && (
          <div className="mb-8 space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">
              Suggested Questions
            </p>
            <div className="space-y-2">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestedQuestion(q)}
                  disabled={loading}
                  className="w-full text-left px-4 py-2 rounded-lg border border-[rgba(142,156,183,0.3)] hover:border-[rgba(142,156,183,0.6)] hover:bg-[rgba(142,156,183,0.05)] text-sm text-[var(--text-primary)] transition-colors disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-lg border border-[rgba(255,75,75,0.3)] bg-[rgba(255,75,75,0.05)] p-4 flex gap-3">
            <AlertCircle className="h-4 w-4 text-[var(--text-negative)] shrink-0 mt-0.5" />
            <p className="text-sm text-[var(--text-negative)]">{error}</p>
          </div>
        )}

        {/* Research Results */}
        {result && (
          <div className="space-y-6">
            {/* Answer Header */}
            <div className="rounded-lg border border-[rgba(142,156,183,0.2)] bg-[rgba(142,156,183,0.05)] p-6">
              <h2 className="text-2xl font-bold mb-1">{result.ticker || ticker}</h2>
              <p className="text-sm text-[var(--text-secondary)] mb-4">{askedQuestion}</p>
              <div className="flex items-center gap-4 text-xs text-[var(--text-secondary)]">
                <span>Confidence: <span className="font-semibold text-[var(--text-primary)]">{result.confidence_score ? `${Math.round(result.confidence_score)}%` : 'N/A'}</span></span>
                <Link href={`/research?t=${ticker}`} className="text-[var(--text-primary)] hover:underline flex items-center gap-1">
                  Full research <LinkIcon className="h-3 w-3" />
                </Link>
              </div>
            </div>

            {/* Executive Answer */}
            {result.business_health?.narrative || result.bull_bear_case?.critical_debate ? (
              <div className="rounded-lg border border-[rgba(142,156,183,0.2)] p-6">
                <h3 className="text-sm font-semibold mb-3 text-[var(--text-primary)]">Assessment</h3>
                <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                  {result.business_health?.narrative || result.bull_bear_case?.critical_debate || 'Analysis pending...'}
                </p>
              </div>
            ) : null}

            {/* Key Evidence Cards */}
            {(result.business_health?.assessment || result.valuation_context?.assessment) && (
              <div className="grid gap-3 sm:grid-cols-2">
                {result.business_health?.assessment && (
                  <div className="rounded-lg border border-[rgba(142,156,183,0.2)] p-4">
                    <p className="text-xs text-[var(--text-secondary)] font-semibold uppercase mb-2">Financial Health</p>
                    <p className="text-base font-semibold text-[var(--text-primary)]">{result.business_health.assessment}</p>
                  </div>
                )}
                {result.valuation_context?.assessment && (
                  <div className="rounded-lg border border-[rgba(142,156,183,0.2)] p-4">
                    <p className="text-xs text-[var(--text-secondary)] font-semibold uppercase mb-2">Valuation</p>
                    <p className="text-base font-semibold text-[var(--text-primary)]">{result.valuation_context.assessment}</p>
                  </div>
                )}
                {result.earnings_quality?.assessment && (
                  <div className="rounded-lg border border-[rgba(142,156,183,0.2)] p-4">
                    <p className="text-xs text-[var(--text-secondary)] font-semibold uppercase mb-2">Earnings Quality</p>
                    <p className="text-base font-semibold text-[var(--text-primary)]">{result.earnings_quality.assessment}</p>
                  </div>
                )}
              </div>
            )}

            {/* Bull & Bear Cases */}
            {(result.bull_bear_case?.bull_case || result.bull_bear_case?.bear_case) && (
              <div className="grid gap-4 sm:grid-cols-2">
                {result.bull_bear_case.bull_case?.thesis && (
                  <div className="rounded-lg border border-[rgba(29,185,84,0.3)] bg-[rgba(29,185,84,0.05)] p-4">
                    <h4 className="text-xs font-semibold uppercase text-[var(--text-secondary)] mb-2 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-[var(--text-positive)]" />
                      Bull Case
                    </h4>
                    <p className="text-sm text-[var(--text-primary)]">{result.bull_bear_case.bull_case.thesis}</p>
                  </div>
                )}
                {result.bull_bear_case.bear_case?.thesis && (
                  <div className="rounded-lg border border-[rgba(255,75,75,0.3)] bg-[rgba(255,75,75,0.05)] p-4">
                    <h4 className="text-xs font-semibold uppercase text-[var(--text-secondary)] mb-2 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-[var(--text-negative)]" />
                      Bear Case
                    </h4>
                    <p className="text-sm text-[var(--text-primary)]">{result.bull_bear_case.bear_case.thesis}</p>
                  </div>
                )}
              </div>
            )}

            {/* Key Risks */}
            {result.risk_engine?.all_risks && result.risk_engine.all_risks.length > 0 && (
              <div className="rounded-lg border border-[rgba(255,75,75,0.2)] p-4">
                <h4 className="text-xs font-semibold uppercase text-[var(--text-secondary)] mb-3">Key Risks</h4>
                <ul className="space-y-2">
                  {result.risk_engine.all_risks.slice(0, 3).map((risk: any, i: number) => (
                    <li key={i} className="text-sm text-[var(--text-primary)] flex gap-2">
                      <span className="text-[var(--text-negative)]">•</span>
                      {risk.title || JSON.stringify(risk).substring(0, 50)}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Catalysts */}
            {result.catalyst_engine?.catalysts && result.catalyst_engine.catalysts.length > 0 && (
              <div className="rounded-lg border border-[rgba(142,156,183,0.2)] p-4">
                <h4 className="text-xs font-semibold uppercase text-[var(--text-secondary)] mb-3">Upcoming Catalysts</h4>
                <ul className="space-y-2">
                  {result.catalyst_engine.catalysts.slice(0, 3).map((cat: any, i: number) => (
                    <li key={i} className="text-sm text-[var(--text-primary)] flex gap-2">
                      <span className="text-[var(--text-secondary)]">→</span>
                      {cat.title || 'Catalyst event'}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Research Links */}
            <div className="rounded-lg border border-[rgba(142,156,183,0.2)] bg-[rgba(142,156,183,0.05)] p-4">
              <p className="text-xs text-[var(--text-secondary)] mb-3">Explore more:</p>
              <div className="flex flex-wrap gap-2">
                {['Overview', 'Financials', 'Valuation', 'Technicals'].map((section) => (
                  <Link
                    key={section}
                    href={`/research?t=${ticker}&tab=${section.toLowerCase()}`}
                    className="px-3 py-1.5 rounded text-xs font-medium border border-[rgba(142,156,183,0.3)] hover:border-[rgba(142,156,183,0.6)] text-[var(--text-primary)] transition-colors"
                  >
                    {section}
                  </Link>
                ))}
              </div>
            </div>

            {/* Raw Evidence Toggle */}
            <div className="border-t border-[rgba(142,156,183,0.2)] pt-6">
              <button
                onClick={() => setShowRawEvidence(!showRawEvidence)}
                className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                <ChevronDown className={`h-4 w-4 transition ${showRawEvidence ? 'rotate-180' : ''}`} />
                View underlying research data
              </button>
              {showRawEvidence && (
                <div className="mt-4 space-y-3">
                  <div className="rounded-lg bg-[rgba(0,0,0,0.3)] p-4 font-mono text-xs overflow-x-auto max-h-64 overflow-y-auto">
                    <pre className="text-[10px]">{JSON.stringify(result, null, 2)}</pre>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)]">
                    Raw research data from all intelligence engines. Displayed analysis above is synthesized from this data.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
