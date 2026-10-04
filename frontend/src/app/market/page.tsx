'use client'

import { API_BASE_URL } from "@/lib/config";
import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { SectionHeader, GlassCard, GlassPanel, MetricCard, LoadingCard, ErrorState, DataFreshnessBadge } from '@/components/glass'

interface MarketSnapshot {
  timestamp: string
  freshness: { as_of: string | null; retrieved_at: string | null; sources: string[]; stale: boolean }
  indices: Record<string, any>
  breadth: { advancers: number; decliners: number; unchanged: number; total: number }
  gainers: Array<{ symbol: string; name: string; price: number; change_pct: number; volume: number }>
  losers: Array<{ symbol: string; name: string; price: number; change_pct: number; volume: number }>
}

export default function MarketPage() {
  const [marketData, setMarketData] = useState<MarketSnapshot | null>(null)
  const [indices, setIndices] = useState<Record<string, any>>({})
  const [breadth, setBreadth] = useState<any>(null)
  const [gainers, setGainers] = useState<any[]>([])
  const [losers, setLosers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/market/overview/snapshot`)
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }
        const result = await response.json()
        if (result.error) {
          setFetchError(result.error)
          return
        }
        setMarketData(result)
        setIndices(result.indices || {})
        setBreadth(result.breadth)
        setGainers(result.gainers || [])
        setLosers(result.losers || [])
        setFetchError(null)
      } catch (err) {
        console.error('Failed to load market data:', err)
        setFetchError('Unable to load market data. Backend may be offline.')
      } finally {
        setLoading(false)
      }
    }

    fetchMarketData()
  }, [])

  if (loading) {
    return (
      <AppLayout>
        <div className="flex-1 px-6 py-12 lg:px-8 max-w-7xl mx-auto">
          <LoadingCard message="Loading market data..." />
        </div>
      </AppLayout>
    )
  }

  if (fetchError) {
    return (
      <AppLayout>
        <div className="flex-1 px-6 py-12 lg:px-8 max-w-7xl mx-auto">
          <ErrorState
            title="Market Data Unavailable"
            description={fetchError}
          />
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="flex-1 px-6 py-12 lg:px-8 max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <SectionHeader
          title="Market Overview"
          subtitle={`End-of-day PSX data (delayed) · ${marketData?.freshness.sources.join(', ') || '—'}`}
          status={<DataFreshnessBadge timestamp={marketData?.freshness.as_of} />}
        />

        {/* Stale Data Warning */}
        {marketData?.freshness.stale && (
          <div className="glass-card border-[var(--warning-soft)] bg-[var(--warning-soft)] p-4">
            <p className="text-sm text-[var(--warning)] font-medium">
              Prices are stale: latest close is {marketData.freshness.as_of}. All figures below are as of that date.
            </p>
          </div>
        )}

        {/* Index Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(indices).map(([code, index]: [string, any]) => {
            if (!index || typeof index.level === 'undefined') {
              return (
                <GlassCard key={code} variant="soft">
                  <div className="text-center">
                    <p className="text-xs font-semibold uppercase text-[var(--text-secondary)] mb-2">{code}</p>
                    <p className="text-2xl font-bold text-[var(--text-muted)] my-2">—</p>
                    <p className="text-xs text-[var(--text-secondary)]">No data</p>
                  </div>
                </GlassCard>
              )
            }
            const isPositive = index.change_pct >= 0
            return (
              <GlassCard key={code} variant="primary" interactive elevation={1}>
                <div className="space-y-3">
                  <p className="text-xs font-semibold uppercase text-[var(--text-secondary)]">{code}</p>
                  <p className="text-3xl font-bold text-[var(--text-primary)]">{index.level?.toFixed(2) || '—'}</p>
                  <div className="flex items-center gap-2 pt-2 border-t border-[rgba(255,255,255,0.3)]">
                    {isPositive ? (
                      <TrendingUp className="w-4 h-4 text-[var(--positive)]" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-[var(--negative)]" />
                    )}
                    <p className={`text-sm font-semibold ${isPositive ? 'text-[var(--positive)]' : 'text-[var(--negative)]'}`}>
                      {isPositive ? '+' : ''}{index.change_pct?.toFixed(2) || '0.00'}%
                    </p>
                    <p className="text-xs text-[var(--text-secondary)]">
                      ({isPositive ? '+' : ''}{index.change?.toFixed(2) || '0.00'})
                    </p>
                  </div>
                </div>
              </GlassCard>
            )
          })}
        </div>

        {/* Market Breadth */}
        {breadth && (
          <GlassPanel title="Market Breadth" className="elevation-2">
            <div className="space-y-6">
              {/* Breadth Metrics */}
              <div className="grid grid-cols-4 gap-4">
                <MetricCard
                  label="Advancers"
                  value={breadth.advancers}
                  status="positive"
                />
                <MetricCard
                  label="Decliners"
                  value={breadth.decliners}
                  status="negative"
                />
                <MetricCard
                  label="Unchanged"
                  value={breadth.unchanged}
                  status="neutral"
                />
                <MetricCard
                  label="Total"
                  value={breadth.total}
                />
              </div>

              {/* Breadth Bar */}
              <div className="space-y-3">
                <div className="h-8 rounded-2xl bg-[rgba(255,255,255,0.3)] overflow-hidden flex shadow-inner">
                  <div
                    className="bg-[var(--positive)]"
                    style={{
                      width: `${(breadth.advancers / breadth.total) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-[var(--negative)]"
                    style={{
                      width: `${(breadth.decliners / breadth.total) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-[var(--text-muted)]"
                    style={{
                      width: `${(breadth.unchanged / breadth.total) * 100}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-[var(--text-secondary)] font-semibold">
                  <span>{((breadth.advancers / breadth.total) * 100).toFixed(1)}%</span>
                  <span>{((breadth.decliners / breadth.total) * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </GlassPanel>
        )}

        {/* Gainers & Losers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Gainers */}
          <GlassPanel title="Top Gainers" className="elevation-1">
            <div className="space-y-3">
              {gainers.length === 0 ? (
                <p className="text-sm text-[var(--text-secondary)] text-center py-8">No data</p>
              ) : (
                gainers.map((stock) => (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between p-3 hover:bg-white/30 rounded-lg transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="font-semibold text-sm text-[var(--text-primary)]">{stock.symbol}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{stock.name || stock.symbol}</p>
                    </div>
                    <div className="text-right flex-shrink-0 ml-4">
                      <p className="text-sm font-semibold text-[var(--text-primary)]">
                        {stock.price?.toFixed(2) || 'N/A'}
                      </p>
                      <p className="text-xs font-semibold text-[var(--positive)]">
                        +{stock.change_pct?.toFixed(2) || '0.00'}%
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </GlassPanel>

          {/* Top Losers */}
          <GlassPanel title="Top Losers" className="elevation-1">
            <div className="space-y-3">
              {losers.length === 0 ? (
                <p className="text-sm text-[var(--text-secondary)] text-center py-8">No data</p>
              ) : (
                losers.map((stock) => (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between p-3 hover:bg-white/30 rounded-lg transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="font-semibold text-sm text-[var(--text-primary)]">{stock.symbol}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{stock.name || stock.symbol}</p>
                    </div>
                    <div className="text-right flex-shrink-0 ml-4">
                      <p className="text-sm font-semibold text-[var(--text-primary)]">
                        {stock.price?.toFixed(2) || 'N/A'}
                      </p>
                      <p className="text-xs font-semibold text-[var(--negative)]">
                        {stock.change_pct?.toFixed(2) || '0.00'}%
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </GlassPanel>
        </div>
      </div>
    </AppLayout>
  )
}
