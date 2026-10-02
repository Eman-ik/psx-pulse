'use client'

import { API_BASE_URL } from "@/lib/config";
import { useEffect, useState } from 'react'


interface MomentumSignal {
  symbol: string
  name: string
  sector: string
  price: number
  return_1m: number | null
  return_3m: number | null
  return_6m: number | null
  return_12m: number | null
  momentum_12_1: number | null
  unavailable: string[]
}

interface Payload {
  freshness: { as_of: string | null; stale: boolean }
  total_screened: number
  max_anchor_gap_days: number
  signals: MomentumSignal[]
}

const COLUMNS = [
  ['return_1m', '1M'],
  ['return_3m', '3M'],
  ['return_6m', '6M'],
  ['return_12m', '12M'],
  ['momentum_12_1', '12-1'],
] as const
type SortKey = (typeof COLUMNS)[number][0]

function Pct({ value }: { value: number | null }) {
  if (value == null) return <span className="text-muted" title="No price close enough to the lookback date">—</span>
  return (
    <span className={`font-semibold ${value >= 0 ? 'text-positive' : 'text-negative'}`}>
      {value > 0 ? '+' : ''}
      {value.toFixed(2)}%
    </span>
  )
}

export default function MomentumScreenerView() {
  const [data, setData] = useState<Payload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('momentum_12_1')

  useEffect(() => {
    fetch(`${API_BASE_URL}/screeners/momentum`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setData)
      .catch(() => setError(`Could not reach the API at ${API_BASE_URL}.`))
  }, [])

  // Rank on one horizon at a time; unavailable values sort last rather than as zero.
  const rows = [...(data?.signals ?? [])].sort((a, b) => (b[sortKey] ?? -Infinity) - (a[sortKey] ?? -Infinity))

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-5">
        <h3 className="text-lg font-bold">Momentum Screener</h3>
        <p className="mt-1 text-xs text-muted">
          Price returns over each horizon{data?.freshness.as_of ? ` to ${data.freshness.as_of}` : ''}, shown side by
          side and never averaged together. 12-1 is the return from 12 months ago to 1 month ago, which skips the most
          recent month.
        </p>
        {data?.freshness.stale && <p className="mt-2 text-xs text-negative">Prices are stale.</p>}
      </div>

      {error && <p className="text-sm text-negative">{error}</p>}

      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        {!rows.length ? (
          <p className="p-8 text-center text-sm text-muted">{data ? 'No securities with return history.' : 'Loading…'}</p>
        ) : (
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted">
                <th className="px-4 py-3 text-left font-medium">Symbol</th>
                {COLUMNS.map(([key, label]) => (
                  <th key={key} className="px-4 py-3 text-right font-medium" aria-sort={sortKey === key ? 'descending' : 'none'}>
                    <button
                      type="button"
                      onClick={() => setSortKey(key)}
                      className={`hover:text-foreground ${sortKey === key ? 'text-foreground underline' : ''}`}
                    >
                      {label}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map((s) => (
                <tr key={s.symbol}>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-accent">{s.symbol}</p>
                    <p className="text-xs text-muted">{s.sector}</p>
                  </td>
                  {COLUMNS.map(([key]) => (
                    <td key={key} className="px-4 py-3 text-right text-xs tabular-nums">
                      <Pct value={s[key]} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && (
        <p className="text-xs text-muted">
          Sorted by {COLUMNS.find(([k]) => k === sortKey)?.[1]}; select a column to re-rank. Returns use unadjusted
          closes, so dividends and bonus issues are excluded. A horizon is blank when no close exists within{' '}
          {data.max_anchor_gap_days} days before its lookback date.
        </p>
      )}
    </div>
  )
}
