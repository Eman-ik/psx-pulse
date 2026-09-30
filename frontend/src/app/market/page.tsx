'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Activity, Wifi, WifiOff } from 'lucide-react'
import Sidebar from '@/components/dashboard/Sidebar'
import Topbar from '@/components/dashboard/Topbar'
import { useMarketRealtime } from '@/hooks/useMarketRealtime'

interface MarketSnapshot {
  timestamp: string
  indices: Record<string, any>
  breadth: { advancers: number; decliners: number; unchanged: number; total: number }
  gainers: Array<{ symbol: string; name: string; price: number; change_pct: number; volume: number }>
  losers: Array<{ symbol: string; name: string; price: number; change_pct: number; volume: number }>
}

export default function MarketPage() {
  const { data: wsData, connected, error } = useMarketRealtime()
  const [marketData, setMarketData] = useState<MarketSnapshot | null>(null)
  const [indices, setIndices] = useState<Record<string, any>>({})
  const [breadth, setBreadth] = useState<any>(null)
  const [gainers, setGainers] = useState<any[]>([])
  const [losers, setLosers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Handle WebSocket updates
  useEffect(() => {
    if (!wsData) return

    if (wsData.type === 'market_update') {
      // Update individual prices
      if (wsData.indices) {
        setIndices((prev) => ({ ...prev, ...wsData.indices }))
      }
    } else if (wsData.type === 'market_snapshot') {
      // Full snapshot update
      setIndices(wsData.data.indices)
      setBreadth(wsData.data.breadth)
      setGainers(wsData.data.gainers)
      setLosers(wsData.data.losers)
      setLoading(false)
    }
  }, [wsData])

  // Fetch initial market data via HTTP
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const response = await fetch('http://localhost:5000/market/overview/snapshot')
        const result = await response.json()
        setMarketData(result)
        setIndices(result.indices)
        setBreadth(result.breadth)
        setGainers(result.gainers)
        setLosers(result.losers)
      } catch (error) {
        console.error('Failed to load market data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchMarketData()
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen w-full bg-bg">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main className="flex-1 px-6 py-6 flex items-center justify-center">
            <div className="text-muted">Loading market data...</div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 px-6 py-6 lg:px-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Market Overview</h1>
              <p className="text-sm text-muted">Real-time PSX market data</p>
            </div>
            <div className="flex items-center gap-2">
              {connected ? (
                <div className="flex items-center gap-2 text-positive">
                  <Wifi className="h-4 w-4" />
                  <span className="text-xs font-semibold">Live</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-muted">
                  <WifiOff className="h-4 w-4" />
                  <span className="text-xs font-semibold">Offline</span>
                </div>
              )}
            </div>
          </div>

          {/* Index Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(indices).map(([code, index]: [string, any]) => (
              <div key={code} className="rounded-lg border border-border bg-surface p-4">
                <p className="text-xs text-muted font-semibold uppercase">{code}</p>
                <p className="text-2xl font-bold mt-2">{index.level.toFixed(2)}</p>
                <div className="flex items-center gap-2 mt-2">
                  {index.change_pct >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-positive" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-negative" />
                  )}
                  <p
                    className={`text-sm font-semibold ${
                      index.change_pct >= 0 ? 'text-positive' : 'text-negative'
                    }`}
                  >
                    {index.change_pct >= 0 ? '+' : ''}
                    {index.change_pct.toFixed(2)}%
                  </p>
                  <p className="text-xs text-muted">
                    ({index.change >= 0 ? '+' : ''}
                    {index.change.toFixed(2)})
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Market Breadth */}
          {breadth && (
            <div className="rounded-lg border border-border bg-surface p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Market Breadth
              </h2>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <p className="text-2xl font-bold text-positive">{breadth.advancers}</p>
                  <p className="text-xs text-muted">Advancers</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-negative">{breadth.decliners}</p>
                  <p className="text-xs text-muted">Decliners</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-muted">{breadth.unchanged}</p>
                  <p className="text-xs text-muted">Unchanged</p>
                </div>
                <div>
                  <p className="text-2xl font-bold">{breadth.total}</p>
                  <p className="text-xs text-muted">Total</p>
                </div>
              </div>
              {/* Breadth Bars */}
              <div className="mt-4 space-y-2">
                <div className="h-6 rounded-full bg-surface-alt overflow-hidden flex">
                  <div
                    className="bg-positive"
                    style={{
                      width: `${(breadth.advancers / breadth.total) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-negative"
                    style={{
                      width: `${(breadth.decliners / breadth.total) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-muted"
                    style={{
                      width: `${(breadth.unchanged / breadth.total) * 100}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted">
                  <span>
                    {((breadth.advancers / breadth.total) * 100).toFixed(1)}%
                  </span>
                  <span>
                    {((breadth.decliners / breadth.total) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Gainers & Losers */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Gainers */}
            <div className="rounded-lg border border-border bg-surface p-6">
              <h2 className="text-lg font-semibold mb-4">Top Gainers</h2>
              <div className="space-y-3">
                {gainers.map((stock) => (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between p-2 hover:bg-surface-alt rounded"
                  >
                    <div>
                      <p className="font-semibold text-sm">{stock.symbol}</p>
                      <p className="text-xs text-muted">{stock.name || stock.symbol}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">
                        {stock.price?.toFixed(2) || 'N/A'}
                      </p>
                      <p className="text-xs text-positive font-semibold">
                        +{stock.change_pct?.toFixed(2) || '0.00'}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Losers */}
            <div className="rounded-lg border border-border bg-surface p-6">
              <h2 className="text-lg font-semibold mb-4">Top Losers</h2>
              <div className="space-y-3">
                {losers.map((stock) => (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between p-2 hover:bg-surface-alt rounded"
                  >
                    <div>
                      <p className="font-semibold text-sm">{stock.symbol}</p>
                      <p className="text-xs text-muted">{stock.name || stock.symbol}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">
                        {stock.price?.toFixed(2) || 'N/A'}
                      </p>
                      <p className="text-xs text-negative font-semibold">
                        {stock.change_pct?.toFixed(2) || '0.00'}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
