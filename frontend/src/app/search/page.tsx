/**
 * Search Page
 *
 * Main entry point for finding companies.
 */
'use client';

import { API_BASE_URL } from "@/lib/config";
import { useEffect, useState } from 'react';
import { SearchBar } from '@/components/SearchBar';

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
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold mb-2">PSX Pulse</h1>
          <p className="text-gray-600">Research built only on data with a known source.</p>
        </div>
      </div>

      {/* Search Section */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold mb-6">Find a Company</h2>
          <SearchBar />

          {statusError && (
            <p className="mt-12 text-sm text-red-700">Data status unavailable: the API at {API_BASE_URL} did not respond.</p>
          )}

          {status && (
            <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <div className="text-2xl font-bold text-blue-600 mb-2">{status.prices.securities}</div>
                <div className="text-gray-700">Securities with daily price history</div>
                <div className="text-sm text-gray-600">
                  {status.prices.bars.toLocaleString()} end-of-day bars from {status.prices.sources.join(', ') || '—'}, latest close{' '}
                  {status.prices.as_of ?? '—'}
                  {status.prices.stale && <span className="text-red-700"> (stale)</span>}
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600 mb-2">{status.fundamentals.statement_facts}</div>
                <div className="text-gray-700">Source-linked financial statement figures</div>
                <div className="text-sm text-gray-600">
                  {status.fundamentals.statement_facts
                    ? `Across ${status.fundamentals.issuers_with_statements} companies`
                    : 'None loaded yet'}
                </div>
              </div>
            </div>
          )}

          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              <strong>About this data:</strong> Prices are delayed end-of-day closes. Every price records the load that
              fetched it, and a financial figure is shown only if it links to the document it came from. Missing data is
              shown as missing, never estimated.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-800 text-gray-300 py-8 mt-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-sm">
            PSX Pulse Research Platform
          </p>
        </div>
      </div>
    </main>
  );
}
