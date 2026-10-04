/**
 * Search Page
 *
 * Main entry point for finding companies.
 */
'use client';

import { API_BASE_URL } from "@/lib/config";
import { useEffect, useState } from 'react';
import { SearchBar } from '@/components/SearchBar';
import { GlassCard, GlassPanel, MetricCard } from '@/components/glass';

type DataStatus = {
  prices: { as_of: string | null; sources: string[]; stale: boolean; bars: number; securities: number };
  fundamentals: { statement_facts: number; issuers_with_statements: number };
};

export default function SearchPage() {
  const [status, setStatus] = useState<DataStatus | null>(null);
  const [statusError, setStatusError] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/data/status`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setStatus)
      .catch(() => setStatusError(true));
  }, []);

  return (
    <main className="min-h-screen bg-[var(--bg-page-deep)]">
      {/* Atmospheric Background */}
      <div className="atmospheric-bg" aria-hidden="true" />
      <div className="grain-overlay" aria-hidden="true" />

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <div className="border-b border-[rgba(142,156,183,0.2)]">
          <div className="max-w-4xl mx-auto px-6 py-12">
            <h1 className="text-4xl font-bold mb-2 text-[var(--text-primary)]">PSX Pulse</h1>
            <p className="text-base text-[var(--text-secondary)]">Research built only on data with a known source.</p>
          </div>
        </div>

        {/* Search Section */}
        <div className="max-w-4xl mx-auto px-6 py-12">
          <GlassPanel title="Find a Company" className="elevation-2">
            <SearchBar />

            {statusError && (
              <p className="mt-8 text-sm text-[var(--negative)]">Data status unavailable: the API at {API_BASE_URL} did not respond.</p>
            )}

            {status && (
              <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                <GlassCard variant="soft">
                  <MetricCard
                    label="Securities"
                    value={status.prices.securities}
                    unit="with price history"
                  />
                  <p className="text-xs text-[var(--text-secondary)] mt-4 pt-4 border-t border-[rgba(255,255,255,0.3)]">
                    {status.prices.bars.toLocaleString()} end-of-day bars from {status.prices.sources.join(', ') || '—'}, latest close{' '}
                    {status.prices.as_of ?? '—'}
                    {status.prices.stale && <span className="text-[var(--negative)]"> (stale)</span>}
                  </p>
                </GlassCard>
                <GlassCard variant="soft">
                  <MetricCard
                    label="Financial Facts"
                    value={status.fundamentals.statement_facts}
                    unit="source-linked"
                  />
                  <p className="text-xs text-[var(--text-secondary)] mt-4 pt-4 border-t border-[rgba(255,255,255,0.3)]">
                    {status.fundamentals.statement_facts
                      ? `Across ${status.fundamentals.issuers_with_statements} companies`
                      : 'None loaded yet'}
                  </p>
                </GlassCard>
              </div>
            )}

            <div className="mt-8 glass-soft p-4">
              <p className="text-sm text-[var(--text-secondary)]">
                <strong className="text-[var(--text-primary)]">About this data:</strong> Prices are delayed end-of-day closes. Every price records the load that
                fetched it, and a financial figure is shown only if it links to the document it came from. Missing data is
                shown as missing, never estimated.
              </p>
            </div>
          </GlassPanel>
        </div>
      </div>
    </main>
  );
}
