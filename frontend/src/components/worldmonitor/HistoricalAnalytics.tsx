"use client";

import React, { useState, useMemo } from 'react';
import { SectorSentiment } from './types';
import { HISTORICAL_CHART_DATA } from './data/mockAndInitialData';
import { SECTOR_SENTIMENT_TRENDS } from './data/heatmapAndSectorData';
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
import { TrendingUp, BarChart3, Layers, Sparkles, Filter, Activity } from 'lucide-react';
import { StrategyBacktester } from './StrategyBacktester';

interface HistoricalAnalyticsProps {
  sectorSentiment: SectorSentiment[];
  onAskAgent?: (promptText: string) => void;
}

export const HistoricalAnalytics: React.FC<HistoricalAnalyticsProps> = ({
  sectorSentiment,
  onAskAgent
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'kse100' | 'brent' | 'pkrUsd' | 'sentimentScore'>('kse100');
  const [selectedSectorFilter, setSelectedSectorFilter] = useState<string>('ALL');

  const sectorColors: Record<string, string> = {
    'Oil & Gas Exploration': '#10b981',
    'Technology & Telecom': '#3b82f6',
    'Cement & Construction': '#8b5cf6',
    'Commercial Banks': '#f59e0b',
    'Fertilizer': '#ec4899',
    'Power Generation': '#06b6d4'
  };

  const combinedSectorData = useMemo(() => {
    const dates = SECTOR_SENTIMENT_TRENDS[0]?.history.map(h => h.date) || [];
    return dates.map((date, idx) => {
      const row: Record<string, any> = { date };
      SECTOR_SENTIMENT_TRENDS.forEach(sec => {
        const point = sec.history[idx];
        if (point) {
          row[sec.sector] = point.score;
        }
      });
      return row;
    });
  }, []);

  const activeSectorData = useMemo(() => {
    if (selectedSectorFilter === 'ALL') return null;
    return SECTOR_SENTIMENT_TRENDS.find(s => s.sector === selectedSectorFilter) || null;
  }, [selectedSectorFilter]);

  const getCorrelationBg = (score: number) => {
    if (score >= 0.7) return 'bg-[#10b981]/15 text-[#10b981] border-[#10b981]/30';
    if (score >= 0.3) return 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/20';
    if (score >= -0.2) return 'bg-[#27272a] text-[#a1a1aa] border-[#3f3f46]';
    return 'bg-[#ef4444]/15 text-[#ef4444] border-[#ef4444]/30';
  };

  return (
    <div className="space-y-6 font-mono">

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
            Analyze historical correlations between KSE-100 benchmark index levels, Brent Crude oil prices, PKR exchange rates, and AI-derived sentiment trajectories across PSX market sectors over time.
          </p>
        </div>

        <div className="flex items-center space-x-1.5 bg-[#18181b] p-1 rounded-md border border-[#27272a] shrink-0 text-xs">
          <button
            onClick={() => setSelectedMetric('kse100')}
            className={`px-3 py-1.5 rounded transition-all ${
              selectedMetric === 'kse100'
                ? 'bg-[#27272a] text-[#fafafa] font-bold border border-[#3f3f46]'
                : 'text-[#a1a1aa] hover:text-[#fafafa]'
            }`}
          >
            KSE-100 Index
          </button>
          <button
            onClick={() => setSelectedMetric('brent')}
            className={`px-3 py-1.5 rounded transition-all ${
              selectedMetric === 'brent'
                ? 'bg-[#27272a] text-[#fafafa] font-bold border border-[#3f3f46]'
                : 'text-[#a1a1aa] hover:text-[#fafafa]'
            }`}
          >
            Brent Crude
          </button>
          <button
            onClick={() => setSelectedMetric('sentimentScore')}
            className={`px-3 py-1.5 rounded transition-all ${
              selectedMetric === 'sentimentScore'
                ? 'bg-[#27272a] text-[#fafafa] font-bold border border-[#3f3f46]'
                : 'text-[#a1a1aa] hover:text-[#fafafa]'
            }`}
          >
            Sentiment Index
          </button>
        </div>
      </div>

      <StrategyBacktester onAskAgent={onAskAgent} />

      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-bold text-[#fafafa] uppercase tracking-wider flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#3b82f6]" />
            <span>KSE-100 vs Macro Drivers & Event Timeline (12-Month)</span>
          </h3>
          <span className="text-xs font-mono text-[#10b981] bg-[#10b981]/10 px-2 py-0.5 rounded border border-[#10b981]/20">
            Current Benchmark: 114,850.40 pts (+0.54%)
          </span>
        </div>

        <div className="h-[340px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={HISTORICAL_CHART_DATA}>
              <defs>
                <linearGradient id="kse100Gradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 11, fill: '#a1a1aa' }} />
              <YAxis yAxisId="left" stroke="#3b82f6" tick={{ fontSize: 11, fill: '#3b82f6' }} domain={['dataMin - 2000', 'dataMax + 2000']} />
              <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" tick={{ fontSize: 11, fill: '#f59e0b' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  borderColor: '#27272a',
                  borderRadius: '6px',
                  color: '#fafafa',
                  fontSize: '12px'
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="kse100"
                name="KSE-100 Index (Pts)"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#kse100Gradient)"
                strokeWidth={2.5}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="brent"
                name="Brent Crude ($/bbl)"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="sentimentScore"
                name="AI Quant Sentiment Score"
                stroke="#10b981"
                strokeWidth={2}
                strokeDasharray="4 4"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="pt-3 border-t border-[#27272a] space-y-2">
          <span className="text-xs font-bold text-[#a1a1aa] uppercase tracking-wider block">
            HISTORICAL EVENT ANNOTATIONS & IMPACT NODES:
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            {HISTORICAL_CHART_DATA.map((item, idx) => (
              <div key={idx} className="p-2 bg-[#18181b] border border-[#27272a] rounded space-y-0.5">
                <span className="text-[10px] text-[#3b82f6] font-bold block">{item.date}</span>
                <span className="text-[11px] text-[#fafafa] font-medium truncate block">{item.event}</span>
                <span className="text-[10px] text-[#a1a1aa]">KSE: {item.kse100.toLocaleString()} pts</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-[#27272a] pb-4">
          <div>
            <div className="flex items-center space-x-2 text-[#3b82f6] text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-[#3b82f6]" />
              <span>PSX SECTOR SENTIMENT TREND VISUALIZER</span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-[#fafafa] font-mono mt-0.5">
              Historical Sector Sentiment Trajectory (-100 to +100)
            </h3>
            <p className="text-xs text-[#a1a1aa] font-sans">
              Select a sector below to inspect its multi-month sentiment score trajectory, article volume, and key catalyst events.
            </p>
          </div>

          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 lg:pb-0 shrink-0">
            <button
              onClick={() => setSelectedSectorFilter('ALL')}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-bold transition-all whitespace-nowrap ${
                selectedSectorFilter === 'ALL'
                  ? 'bg-[#3b82f6] text-white shadow-xs'
                  : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'
              }`}
            >
              All Sectors (Comparative Overlay)
            </button>
            {SECTOR_SENTIMENT_TRENDS.map(sec => (
              <button
                key={sec.sector}
                onClick={() => setSelectedSectorFilter(sec.sector)}
                className={`px-2.5 py-1.5 rounded-md text-xs font-mono font-medium transition-all whitespace-nowrap flex items-center space-x-1.5 ${
                  selectedSectorFilter === sec.sector
                    ? 'bg-[#27272a] text-[#fafafa] border border-[#3f3f46] font-bold'
                    : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'
                }`}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: sec.color }} />
                <span>{sec.sector}</span>
              </button>
            ))}
          </div>
        </div>

        {selectedSectorFilter === 'ALL' ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-[#a1a1aa]">
              <span>Comparing AI Sentiment Trajectory Across All 6 PSX Major Sectors</span>
              <span className="text-[#3b82f6]">Baseline: 0 (Neutral Sentiment)</span>
            </div>

            <div className="h-[360px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={combinedSectorData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 11, fill: '#a1a1aa' }} />
                  <YAxis stroke="#a1a1aa" tick={{ fontSize: 11, fill: '#a1a1aa' }} domain={[-40, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#18181b',
                      borderColor: '#27272a',
                      borderRadius: '6px',
                      color: '#fafafa',
                      fontSize: '12px'
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <ReferenceLine y={0} stroke="#3f3f46" strokeDasharray="3 3" label={{ value: 'NEUTRAL (0)', fill: '#a1a1aa', fontSize: 10 }} />
                  <ReferenceLine y={50} stroke="#10b981" strokeDasharray="2 2" opacity={0.4} />

                  {SECTOR_SENTIMENT_TRENDS.map(sec => (
                    <Line
                      key={sec.sector}
                      type="monotone"
                      dataKey={sec.sector}
                      name={sec.sector}
                      stroke={sec.color}
                      strokeWidth={2.5}
                      dot={{ r: 3 }}
                      activeDot={{ r: 6 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          activeSectorData && (
            <div className="space-y-5">

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#18181b] p-3 rounded-md border border-[#27272a] text-xs">
                <div>
                  <span className="text-[#a1a1aa] block text-[10px]">SELECTED SECTOR</span>
                  <span className="text-[#fafafa] font-bold text-sm">{activeSectorData.sector}</span>
                </div>
                <div>
                  <span className="text-[#a1a1aa] block text-[10px]">LATEST SENTIMENT SCORE</span>
                  <span className="text-[#10b981] font-bold text-sm">
                    +{activeSectorData.history[activeSectorData.history.length - 1].score} / 100
                  </span>
                </div>
                <div>
                  <span className="text-[#a1a1aa] block text-[10px]">6-MONTH CHANGE</span>
                  <span className="text-[#3b82f6] font-bold text-sm">
                    +{(activeSectorData.history[activeSectorData.history.length - 1].score - activeSectorData.history[0].score)} pts
                  </span>
                </div>
                <div>
                  <span className="text-[#a1a1aa] block text-[10px]">TOTAL NEWS ARTICLES</span>
                  <span className="text-[#fafafa] font-bold text-sm">
                    {activeSectorData.history.reduce((acc, curr) => acc + curr.newsCount, 0)} Items
                  </span>
                </div>
              </div>

              <div className="h-[320px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={activeSectorData.history}>
                    <defs>
                      <linearGradient id="singleSectorGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={activeSectorData.color} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={activeSectorData.color} stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 11, fill: '#a1a1aa' }} />
                    <YAxis yAxisId="score" stroke={activeSectorData.color} tick={{ fontSize: 11, fill: activeSectorData.color }} domain={[-30, 100]} />
                    <YAxis yAxisId="volume" orientation="right" stroke="#a1a1aa" tick={{ fontSize: 11, fill: '#a1a1aa' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#18181b',
                        borderColor: '#27272a',
                        borderRadius: '6px',
                        color: '#fafafa',
                        fontSize: '12px'
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <ReferenceLine yAxisId="score" y={0} stroke="#3f3f46" strokeDasharray="3 3" />

                    <Bar
                      yAxisId="volume"
                      dataKey="newsCount"
                      name="News Volume (Articles)"
                      fill="#27272a"
                      radius={[4, 4, 0, 0]}
                    />
                    <Area
                      yAxisId="score"
                      type="monotone"
                      dataKey="score"
                      name="AI Sentiment Score (-100 to +100)"
                      stroke={activeSectorData.color}
                      fillOpacity={1}
                      fill="url(#singleSectorGradient)"
                      strokeWidth={3}
                      dot={{ r: 4, fill: activeSectorData.color }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-2 pt-2 border-t border-[#27272a]">
                <span className="text-xs font-bold text-[#fafafa] uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-[#3b82f6]" />
                  <span>MONTHLY CATALYSTS & GEOPOLITICAL DRIVERS FOR {activeSectorData.sector.toUpperCase()}:</span>
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs">
                  {activeSectorData.history.map((pt, idx) => (
                    <div key={idx} className="p-2.5 bg-[#18181b] border border-[#27272a] rounded space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold text-[#3b82f6]">{pt.date}</span>
                        <span className="text-[10px] font-bold text-[#10b981] bg-[#10b981]/10 px-1.5 py-0.2 rounded">
                          +{pt.score} pts
                        </span>
                      </div>
                      <p className="text-[11px] text-[#fafafa] font-sans leading-tight">
                        {pt.keyEvent}
                      </p>
                      <div className="text-[10px] text-[#a1a1aa] flex justify-between">
                        <span>Bullish Ratio: {Math.round(pt.bullishRatio * 100)}%</span>
                        <span>{pt.newsCount} articles</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )
        )}

      </div>

      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#fafafa] uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#3b82f6]" />
            <span>PSX Sector Sentiment & Macro Correlation Heatmap</span>
          </h3>
          <span className="text-xs text-[#a1a1aa]">
            Updated via Real-time AI Sentiment Models
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sectorSentiment.map((sec) => (
            <div
              key={sec.sector}
              className="p-4 bg-[#18181b] border border-[#27272a] rounded-lg space-y-3 hover:border-[#3f3f46] transition-all"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-[#fafafa] text-sm">
                  {sec.sector}
                </h4>
                <span className="text-xs font-bold text-[#10b981]">
                  {sec.weeklyChange}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span
                  className={`text-xs font-bold px-2.5 py-0.5 rounded border ${
                    sec.sentiment === 'BULLISH'
                      ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30'
                      : sec.sentiment === 'BEARISH'
                      ? 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30'
                      : 'bg-[#27272a] text-[#a1a1aa] border-[#3f3f46]'
                  }`}
                >
                  {sec.score > 0 ? `+${sec.score}` : sec.score} {sec.sentiment}
                </span>

                <span
                  className={`text-[10px] px-2 py-0.5 rounded border ${getCorrelationBg(sec.correlationToMacro)}`}
                  title="Correlation to Macro & Geopolitical Drivers (-1.0 to +1.0)"
                >
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
      </div>

    </div>
  );
};
