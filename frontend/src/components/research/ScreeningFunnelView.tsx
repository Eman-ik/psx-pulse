'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { BarChart3, TrendingDown, TrendingUp, Target, Users, ChevronDown, ChevronUp, AlertCircle, CheckCircle, ExternalLink } from 'lucide-react'

interface ScreeningResult {
  symbol: string
  name: string
  sector: string
  stage_reached: number
  screen_1: {
    passes: boolean
    reasons: string[]
  }
  screen_2: {
    passes: boolean | null
    score: number
    reasons: string[]
  } | null
  screen_3: {
    passes: boolean | null
    score: number
    reasons: string[]
  } | null
  screen_4: {
    passes: boolean | null
    score: number
    reasons: string[]
  } | null
}

interface WatchlistCompany {
  rank: number
  symbol: string
  name: string
  sector: string
  composite_score: number
  screen_2_score: number
  screen_3_score: number
  screen_4_score: number
}

interface ScreeningData {
  session: {
    created_at: string
    ticker_count: number
    passed_screen_1: number
    passed_screen_2: number
    passed_screen_3: number
    passed_screen_4: number
    watchlist_count: number
  }
  funnel: {
    screen_1: number
    screen_2: number
    screen_3: number
    screen_4: number
    watchlist: number
  }
  watchlist: WatchlistCompany[]
  details: ScreeningResult[]
}

const SCREEN_LABELS = {
  1: 'Basic Quality',
  2: 'Financial Quality',
  3: 'Valuation',
  4: 'Peer Comparison',
  5: 'Watchlist',
}

const SCREEN_ICONS = {
  1: AlertCircle,
  2: TrendingUp,
  3: Target,
  4: Users,
  5: BarChart3,
}

export function ScreeningFunnelView() {
  const [data, setData] = useState<ScreeningData | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedCompany, setExpandedCompany] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'funnel' | 'watchlist' | 'details'>('watchlist')

  useEffect(() => {
    const runScreening = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/screening/run')
        const result = await response.json()
        setData(result)
      } catch (error) {
        console.error('Screening failed:', error)
      } finally {
        setLoading(false)
      }
    }

    runScreening()
  }, [])

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8">
        <div className="flex items-center justify-center gap-2 text-sm text-muted">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-r-transparent"></div>
          Running screening funnel...
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8 text-center text-sm text-muted">
        Could not load screening data
      </div>
    )
  }

  const escapeRatio = (passed: number, total: number) => passed / total
  const passRate = (i: number) => {
    const totals = [
      data.session.ticker_count,
      data.session.passed_screen_1,
      data.session.passed_screen_2,
      data.session.passed_screen_3,
    ]
    return Math.round((data.funnel[`screen_${i}` as keyof typeof data.funnel] / totals[i - 1]) * 100)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-border bg-surface p-5">
        <h3 className="text-lg font-bold">Fundamental Analysis Screening Funnel</h3>
        <p className="mt-1 text-xs text-muted">
          5-stage screening across {data.session.ticker_count} companies (Fertilizer + Cement)
        </p>
        <p className="mt-2 text-xs text-muted">
          Run Date: {new Date(data.session.created_at).toLocaleDateString()}
        </p>
      </div>

      {/* Funnel Visualization */}
      <div className="rounded-lg border border-border bg-surface p-5">
        <h4 className="mb-4 text-sm font-bold">Screening Funnel</h4>

        <div className="space-y-3">
          {[1, 2, 3, 4].map((stage) => {
            const Icon = SCREEN_ICONS[stage as keyof typeof SCREEN_ICONS]
            const passed = data.funnel[`screen_${stage}` as keyof typeof data.funnel]
            const total = stage === 1 ? data.session.ticker_count : data.funnel[`screen_${stage - 1}` as keyof typeof data.funnel]
            const rate = passRate(stage)
            const width = stage === 1 ? 100 : (passed / data.session.ticker_count) * 100

            return (
              <div key={stage} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-accent" />
                    <span className="text-xs font-semibold">{SCREEN_LABELS[stage as keyof typeof SCREEN_LABELS]}</span>
                  </div>
                  <div className="text-xs text-muted">
                    <span className="font-mono">{passed}</span> passed
                    <span className="mx-1">·</span>
                    <span className="font-mono">{rate}%</span>
                  </div>
                </div>
                <div className="h-2 rounded-full bg-surface-alt overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-accent to-accent/60 transition-all"
                    style={{ width: `${width}%` }}
                  ></div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-3 gap-3 border-t border-border pt-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-accent">{data.session.watchlist_count}</p>
            <p className="text-xs text-muted">Watchlist Companies</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{Math.round((data.session.watchlist_count / data.session.ticker_count) * 100)}%</p>
            <p className="text-xs text-muted">Pass All Screens</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{data.session.ticker_count}</p>
            <p className="text-xs text-muted">Total Universe</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {(['watchlist', 'funnel', 'details'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`border-b-2 px-3 py-2 text-xs font-semibold transition-colors ${
              activeTab === tab
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:text-foreground'
            }`}
          >
            {tab === 'watchlist' && `Watchlist (${data.session.watchlist_count})`}
            {tab === 'funnel' && 'Funnel Stats'}
            {tab === 'details' && 'Company Details'}
          </button>
        ))}
      </div>

      {/* Watchlist Tab */}
      {activeTab === 'watchlist' && (
        <div className="rounded-lg border border-border bg-surface overflow-hidden">
          {data.watchlist.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted">
              No companies passed all screening stages
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-muted">
                  <th className="px-4 py-3 text-left font-medium">#</th>
                  <th className="px-4 py-3 text-left font-medium">Symbol</th>
                  <th className="px-4 py-3 text-left font-medium">Company</th>
                  <th className="px-4 py-3 text-left font-medium">Sector</th>
                  <th className="px-4 py-3 text-center font-medium">Composite</th>
                  <th className="px-4 py-3 text-center font-medium">Financial</th>
                  <th className="px-4 py-3 text-center font-medium">Valuation</th>
                  <th className="px-4 py-3 text-center font-medium">Peer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.watchlist.map((company) => (
                  <tr key={company.symbol} className="hover:bg-surface-alt/50">
                    <td className="px-4 py-3 text-xs text-muted tabular-nums font-bold">{company.rank}</td>
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-accent">{company.symbol}</td>
                    <td className="px-4 py-3">{company.name}</td>
                    <td className="px-4 py-3 text-xs text-muted">{company.sector}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs font-bold ${
                        company.composite_score >= 70 ? 'text-positive' :
                        company.composite_score >= 50 ? 'text-accent' : 'text-negative'
                      }`}>
                        {company.composite_score.toFixed(0)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-xs">{company.screen_2_score.toFixed(0)}</td>
                    <td className="px-4 py-3 text-center text-xs">{company.screen_3_score.toFixed(0)}</td>
                    <td className="px-4 py-3 text-center text-xs">{company.screen_4_score.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Details Tab */}
      {activeTab === 'details' && (
        <div className="space-y-3">
          {data.details.map((company) => (
            <div key={company.symbol} className="rounded-lg border border-border bg-surface overflow-hidden">
              {/* Header */}
              <button
                onClick={() => setExpandedCompany(expandedCompany === company.symbol ? null : company.symbol)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-alt/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-surface-alt flex items-center justify-center">
                    {company.stage_reached === 5 ? (
                      <CheckCircle className="h-4 w-4 text-positive" />
                    ) : (
                      <span className="text-xs font-bold text-muted">{company.stage_reached}</span>
                    )}
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-semibold">{company.symbol} — {company.name}</p>
                    <p className="text-xs text-muted">{company.sector}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted">
                    {company.stage_reached === 5 ? '✓ Watchlist' : `Failed Screen ${company.stage_reached}`}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${expandedCompany === company.symbol ? 'rotate-180' : ''}`}
                  />
                </div>
              </button>

              {/* Expanded Details */}
              {expandedCompany === company.symbol && (
                <div className="border-t border-border px-4 py-3 space-y-3 bg-surface-alt/30">
                  {/* Screen 1 */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle className="h-4 w-4 text-muted" />
                      <p className="text-xs font-semibold">Screen 1: Basic Quality</p>
                      <span className={`text-xs font-semibold ${company.screen_1.passes ? 'text-positive' : 'text-negative'}`}>
                        {company.screen_1.passes ? '✓ PASS' : '✗ FAIL'}
                      </span>
                    </div>
                    {company.screen_1.reasons.length > 0 && (
                      <ul className="ml-6 space-y-1 text-xs text-muted">
                        {company.screen_1.reasons.map((reason, i) => (
                          <li key={i}>• {reason}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Screen 2 */}
                  {company.screen_2 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="h-4 w-4 text-muted" />
                        <p className="text-xs font-semibold">Screen 2: Financial Quality</p>
                        <span className={`text-xs font-semibold ${
                          company.screen_2.passes ? 'text-positive' : company.screen_2.passes === null ? 'text-muted' : 'text-negative'
                        }`}>
                          {company.screen_2.passes === null ? 'N/A' : company.screen_2.passes ? '✓ PASS' : '✗ FAIL'}
                        </span>
                        <span className="text-xs text-muted font-mono">{company.screen_2.score.toFixed(0)}/100</span>
                      </div>
                      {company.screen_2.reasons.length > 0 && (
                        <ul className="ml-6 space-y-1 text-xs text-muted">
                          {company.screen_2.reasons.map((reason, i) => (
                            <li key={i}>• {reason}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* Screen 3 */}
                  {company.screen_3 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="h-4 w-4 text-muted" />
                        <p className="text-xs font-semibold">Screen 3: Valuation</p>
                        <span className={`text-xs font-semibold ${
                          company.screen_3.passes ? 'text-positive' : company.screen_3.passes === null ? 'text-muted' : 'text-negative'
                        }`}>
                          {company.screen_3.passes === null ? 'N/A' : company.screen_3.passes ? '✓ PASS' : '✗ FAIL'}
                        </span>
                        <span className="text-xs text-muted font-mono">{company.screen_3.score.toFixed(0)}/100</span>
                      </div>
                      {company.screen_3.reasons.length > 0 && (
                        <ul className="ml-6 space-y-1 text-xs text-muted">
                          {company.screen_3.reasons.map((reason, i) => (
                            <li key={i}>• {reason}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* Screen 4 */}
                  {company.screen_4 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Users className="h-4 w-4 text-muted" />
                        <p className="text-xs font-semibold">Screen 4: Peer Comparison</p>
                        <span className={`text-xs font-semibold ${
                          company.screen_4.passes ? 'text-positive' : company.screen_4.passes === null ? 'text-muted' : 'text-negative'
                        }`}>
                          {company.screen_4.passes === null ? 'N/A' : company.screen_4.passes ? '✓ PASS' : '✗ FAIL'}
                        </span>
                        <span className="text-xs text-muted font-mono">{company.screen_4.score.toFixed(0)}/100</span>
                      </div>
                      {company.screen_4.reasons.length > 0 && (
                        <ul className="ml-6 space-y-1 text-xs text-muted">
                          {company.screen_4.reasons.map((reason, i) => (
                            <li key={i}>• {reason}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="border-t border-border pt-3 flex gap-2">
                    <Link
                      href={`/screener?symbol=${company.symbol}`}
                      className="flex-1 inline-flex items-center justify-center gap-2 rounded-md bg-accent/10 px-3 py-2 text-xs font-semibold text-accent hover:bg-accent/20 transition-colors"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View in Screener
                    </Link>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
