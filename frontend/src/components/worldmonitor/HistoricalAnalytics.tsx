"use client";

import React, { useState, useMemo } from 'react';
import { SectorSentiment } from './types';
import type { NewsAnnouncement } from '@/lib/api';
import {
  ResponsiveContainer,
  ComposedChart,
  LineChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Area,
  ReferenceLine
} from 'recharts';
import { TrendingUp, BarChart3, Sparkles, Activity, Grid3X3 } from 'lucide-react';
import { StrategyBacktester } from './StrategyBacktester';

interface HistoricalAnalyticsProps {
  sectorSentiment: SectorSentiment[];
  realAnnouncements?: NewsAnnouncement[];
  companyById?: Record<number, { name: string; symbol: string | null }>;
  onAskAgent?: (promptText: string) => void;
}

const COMPANY_COLORS: Record<string, string> = {
  FFC: '#3b82f6',
  EFERT: '#10b981',
  FATIMA: '#f59e0b',
  AGL: '#8b5cf6',
  AHCL: '#ec4899',
};

export const HistoricalAnalytics: React.FC<HistoricalAnalyticsProps> = ({
  sectorSentiment,
  realAnnouncements = [],
  companyById = {},
  onAskAgent
}) => {
  const [selectedCompanyFilter, setSelectedCompanyFilter] = useState<string>('ALL');

  const { monthlyData, companyMonthlyData, availableCompanies } = useMemo(() => {
    type MonthEntry = { count: number; totalSentiment: number; byCategory: Record<string, number> };
    type CompanyMonthEntry = { count: number; totalSentiment: number };

    const monthMap = new Map<string, MonthEntry>();
    const companyMonthMap = new Map<string, Map<string, CompanyMonthEntry>>();
    const companySet = new Set<string>();

    for (const a of realAnnouncements) {
      const month = a.published_at.slice(0, 7);
      const ticker = a.issuer_id != null ? (companyById[a.issuer_id]?.symbol ?? 'UNK') : 'UNK';
      const score = a.sentiment_score ?? 0;

      if (!monthMap.has(month)) monthMap.set(month, { count: 0, totalSentiment: 0, byCategory: {} });
      const entry = monthMap.get(month)!;
      entry.count++;
      entry.totalSentiment += score;
      entry.byCategory[a.category] = (entry.byCategory[a.category] ?? 0) + 1;

      companySet.add(ticker);
      if (!companyMonthMap.has(ticker)) companyMonthMap.set(ticker, new Map());
      const cm = companyMonthMap.get(ticker)!;
      if (!cm.has(month)) cm.set(month, { count: 0, totalSentiment: 0 });
      const ce = cm.get(month)!;
      ce.count++;
      ce.totalSentiment += score;
    }

    const sortedMonths = Array.from(monthMap.keys()).sort();

    const monthlyData = sortedMonths.map(month => {
      const e = monthMap.get(month)!;
      return {
        date: month.slice(2),
        fullDate: month,
        count: e.count,
        avgSentiment: e.count > 0 ? +(e.totalSentiment / e.count * 100).toFixed(1) : 0,
        results: e.byCategory['results'] ?? 0,
        payout: e.byCategory['payout'] ?? 0,
        leadership: e.byCategory['leadership'] ?? 0,
        other: (e.byCategory['regulatory'] ?? 0) + (e.byCategory['operations'] ?? 0) + (e.byCategory['general'] ?? 0),
      };
    });

    const companyMonthlyData = sortedMonths.map(month => {
      const row: Record<string, string | number> = { date: month.slice(2) };
      companyMonthMap.forEach((cm, ticker) => {
        const ce = cm.get(month);
        row[ticker] = ce ? +(ce.totalSentiment / ce.count * 100).toFixed(1) : 0;
      });
      return row;
    });

    const availableCompanies = Array.from(companySet).filter(t => t !== 'UNK').sort();

    return { monthlyData, companyMonthlyData, availableCompanies };
  }, [realAnnouncements, companyById]);

  const getCorrelationBg = (score: number) => {
    if (score >= 0.7) return 'bg-[#10b981]/15 text-[#10b981] border-[#10b981]/30';
    if (score >= 0.3) return 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/20';
    if (score >= -0.2) return 'bg-[#27272a] text-[#a1a1aa] border-[#3f3f46]';
    return 'bg-[#ef4444]/15 text-[#ef4444] border-[#ef4444]/30';
  };

  const filteredCompanyData = selectedCompanyFilter === 'ALL'
    ? companyMonthlyData
    : companyMonthlyData;

  const activeCompanies = selectedCompanyFilter === 'ALL'
    ? availableCompanies
    : [selectedCompanyFilter];

  return (
    <div className="space-y-6 font-mono">

      {/* Header */}
      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center space-x-2 text-[#3b82f6] text-xs font-semibold uppercase tracking-wider mb-1">
            <BarChart3 className="w-4 h-4 text-[#3b82f6]" />
            <span>QUANTITATIVE HISTORICAL ENGINE</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-[#fafafa] font-mono">
            PSX Historical Data & Sector Sentiment Analytics
          </h2>
          <p className="text-[#a1a1aa] text-xs font-sans mt-1 max-w-3xl">
            Real announcement volume and keyword-derived sentiment trends for the fertilizer sector pilot (FFC, EFERT, FATIMA, AGL, AHCL). Data sourced from 91 official PSX filings in the research DB.
          </p>
        </div>
        <span className="text-xs font-mono text-[#10b981] bg-[#10b981]/10 px-3 py-1 rounded border border-[#10b981]/20 shrink-0">
          {realAnnouncements.length} real DB filings
        </span>
      </div>

      <StrategyBacktester onAskAgent={onAskAgent} />

      {/* Chart 1: Monthly Announcement Volume & Sentiment */}
      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-bold text-[#fafafa] uppercase tracking-wider flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#3b82f6]" />
            <span>Monthly Announcement Volume & Sentiment — Fertilizer Sector</span>
          </h3>
          <span className="text-[10px] text-[#a1a1aa] font-mono">Keyword sentiment · not AI/LLM</span>
        </div>

        {monthlyData.length > 0 ? (
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={monthlyData}>
                <defs>
                  <linearGradient id="sentGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 10, fill: '#a1a1aa' }} />
                <YAxis yAxisId="left" stroke="#10b981" tick={{ fontSize: 10, fill: '#10b981' }} />
                <YAxis yAxisId="right" orientation="right" stroke="#3b82f6" tick={{ fontSize: 10, fill: '#3b82f6' }} domain={[-100, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '6px', color: '#fafafa', fontSize: '11px' }}
                  formatter={(value, name) => [
                    name === 'Avg Sentiment (×100)' && typeof value === 'number' ? `${value > 0 ? '+' : ''}${value}` : value,
                    name
                  ]}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar yAxisId="left" dataKey="results" name="Results" stackId="a" fill="#3b82f6" opacity={0.8} />
                <Bar yAxisId="left" dataKey="payout" name="Payout/Div" stackId="a" fill="#10b981" opacity={0.8} />
                <Bar yAxisId="left" dataKey="leadership" name="Leadership" stackId="a" fill="#f59e0b" opacity={0.8} />
                <Bar yAxisId="left" dataKey="other" name="Other" stackId="a" fill="#6b7280" opacity={0.7} />
                <ReferenceLine yAxisId="right" y={0} stroke="#3f3f46" strokeDasharray="3 3" />
                <Area
                  yAxisId="right"
                  type="monotone"
                  dataKey="avgSentiment"
                  name="Avg Sentiment (×100)"
                  stroke="#3b82f6"
                  fill="url(#sentGradient)"
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#3b82f6' }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-[200px] flex items-center justify-center text-[#a1a1aa] text-xs">
            No announcement data — check backend connection.
          </div>
        )}

        {monthlyData.length > 0 && (
          <div className="pt-2 border-t border-[#27272a] grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            {monthlyData.slice(-4).map((item, idx) => (
              <div key={idx} className="p-2 bg-[#18181b] border border-[#27272a] rounded space-y-0.5">
                <span className="text-[10px] text-[#3b82f6] font-bold block">{item.fullDate}</span>
                <span className="text-[11px] text-[#fafafa] font-medium block">{item.count} announcements</span>
                <span className={`text-[10px] font-bold ${item.avgSentiment > 0 ? 'text-[#10b981]' : item.avgSentiment < 0 ? 'text-[#ef4444]' : 'text-[#a1a1aa]'}`}>
                  Sentiment: {item.avgSentiment > 0 ? '+' : ''}{item.avgSentiment}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Chart 2: Per-company sentiment trend */}
      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-[#27272a] pb-4">
          <div>
            <div className="flex items-center space-x-2 text-[#3b82f6] text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-[#3b82f6]" />
              <span>PER-COMPANY SENTIMENT TREND — FERTILIZER PILOT</span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-[#fafafa] font-mono mt-0.5">
              Monthly Keyword Sentiment by Company (×100)
            </h3>
            <p className="text-xs text-[#a1a1aa] font-sans">
              Filter by company to inspect monthly sentiment trajectory derived from official PSX announcement headlines.
            </p>
          </div>

          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 lg:pb-0 shrink-0">
            <button
              onClick={() => setSelectedCompanyFilter('ALL')}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-bold transition-all whitespace-nowrap ${
                selectedCompanyFilter === 'ALL'
                  ? 'bg-[#3b82f6] text-white shadow-xs'
                  : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'
              }`}
            >
              All Companies
            </button>
            {availableCompanies.map(ticker => (
              <button
                key={ticker}
                onClick={() => setSelectedCompanyFilter(ticker)}
                className={`px-2.5 py-1.5 rounded-md text-xs font-mono font-medium transition-all whitespace-nowrap flex items-center space-x-1.5 ${
                  selectedCompanyFilter === ticker
                    ? 'bg-[#27272a] text-[#fafafa] border border-[#3f3f46] font-bold'
                    : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'
                }`}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COMPANY_COLORS[ticker] ?? '#6b7280' }} />
                <span>${ticker}</span>
              </button>
            ))}
          </div>
        </div>

        {companyMonthlyData.length > 0 ? (
          <div className="h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={filteredCompanyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 10, fill: '#a1a1aa' }} />
                <YAxis stroke="#a1a1aa" tick={{ fontSize: 10, fill: '#a1a1aa' }} domain={[-100, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '6px', color: '#fafafa', fontSize: '11px' }}
                  formatter={(value, name) => [typeof value === 'number' ? `${value > 0 ? '+' : ''}${value}` : value, `$${name}`]}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <ReferenceLine y={0} stroke="#3f3f46" strokeDasharray="3 3" label={{ value: 'Neutral (0)', fill: '#a1a1aa', fontSize: 9 }} />
                <ReferenceLine y={20} stroke="#10b981" strokeDasharray="2 2" opacity={0.3} />
                <ReferenceLine y={-20} stroke="#ef4444" strokeDasharray="2 2" opacity={0.3} />
                {activeCompanies.map(ticker => (
                  <Line
                    key={ticker}
                    type="monotone"
                    dataKey={ticker}
                    name={ticker}
                    stroke={COMPANY_COLORS[ticker] ?? '#6b7280'}
                    strokeWidth={2.5}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-[200px] flex items-center justify-center text-[#a1a1aa] text-xs">
            No announcement data — check backend connection.
          </div>
        )}

        {availableCompanies.length > 0 && (
          <div className="pt-3 border-t border-[#27272a] space-y-2">
            <span className="text-xs font-bold text-[#fafafa] uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#3b82f6]" />
              <span>COMPANY ANNOUNCEMENT BREAKDOWN:</span>
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
              {availableCompanies.map(ticker => {
                const co = Object.values(companyById).find(c => c.symbol === ticker);
                const count = realAnnouncements.filter(a => a.issuer_id != null && companyById[a.issuer_id]?.symbol === ticker).length;
                const scores = realAnnouncements
                  .filter(a => a.issuer_id != null && companyById[a.issuer_id]?.symbol === ticker && a.sentiment_score != null)
                  .map(a => a.sentiment_score!);
                const avg = scores.length > 0 ? scores.reduce((s, v) => s + v, 0) / scores.length : 0;
                return (
                  <div key={ticker} className="p-2 bg-[#18181b] border border-[#27272a] rounded space-y-1">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COMPANY_COLORS[ticker] ?? '#6b7280' }} />
                      <span className="font-bold text-[#fafafa]">${ticker}</span>
                    </div>
                    <span className="text-[#a1a1aa] block">{count} filings</span>
                    <span className={`font-bold text-[10px] ${avg > 0.02 ? 'text-[#10b981]' : avg < -0.02 ? 'text-[#ef4444]' : 'text-[#a1a1aa]'}`}>
                      Avg: {avg > 0 ? '+' : ''}{(avg * 100).toFixed(1)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Sector Sentiment Heatmap (from sectorSentiment prop — real API) */}
      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#fafafa] uppercase tracking-wider flex items-center gap-2">
            <Grid3X3 className="w-4 h-4 text-[#3b82f6]" />
            <span>Sector Sentiment Overview</span>
          </h3>
          <span className="text-[10px] text-[#a1a1aa] font-mono">From sector intelligence API</span>
        </div>

        {sectorSentiment.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sectorSentiment.map((sec) => (
              <div
                key={sec.sector}
                className="p-4 bg-[#18181b] border border-[#27272a] rounded-lg space-y-3 hover:border-[#3f3f46] transition-all"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-[#fafafa] text-sm">{sec.sector}</h4>
                  <span className="text-xs font-bold text-[#10b981]">{sec.weeklyChange}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className={`text-xs font-bold px-2.5 py-0.5 rounded border ${
                    sec.sentiment === 'BULLISH'
                      ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30'
                      : sec.sentiment === 'BEARISH'
                      ? 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30'
                      : 'bg-[#27272a] text-[#a1a1aa] border-[#3f3f46]'
                  }`}>
                    {sec.score > 0 ? `+${sec.score}` : sec.score} {sec.sentiment}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded border ${getCorrelationBg(sec.correlationToMacro)}`}>
                    CORR: {sec.correlationToMacro > 0 ? `+${sec.correlationToMacro}` : sec.correlationToMacro}
                  </span>
                </div>

                <p className="text-xs text-[#a1a1aa] font-sans leading-normal">
                  <strong className="text-[#fafafa] font-mono">Driver:</strong> {sec.keyDriver}
                </p>

                <div className="flex items-center space-x-1.5 pt-1">
                  <span className="text-[10px] text-[#a1a1aa]">Key constituents:</span>
                  {sec.topTickers.map((t) => (
                    <span key={t} className="text-[10px] font-bold bg-[#27272a] text-[#3b82f6] px-1.5 py-0.5 rounded">
                      ${t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-[#a1a1aa] text-xs py-8">
            No sector sentiment data available.
          </div>
        )}
      </div>

    </div>
  );
};
