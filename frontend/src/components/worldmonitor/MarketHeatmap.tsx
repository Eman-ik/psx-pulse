"use client";

import React, { useState, useMemo } from 'react';
import { PSX_HEATMAP_DATA, EXECUTIVE_MACRO_GEOPOLITICAL_STATUS } from './data/heatmapAndSectorData';
import { HeatmapStockItem } from './types';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import {
  Grid,
  TrendingUp,
  TrendingDown,
  Search,
  Sparkles,
  X,
  BarChart2,
  Bot,
  Layers,
  ShieldCheck,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Globe,
  ShieldAlert,
  DollarSign,
  Award,
  CheckCircle2,
  AlertTriangle,
  Filter,
  PieChart,
  Info,
  Building2,
  Target,
  BarChart3,
  RefreshCw,
  GitCompare,
  Activity,
  Sliders,
  Check,
  Percent,
  Gauge
} from 'lucide-react';

interface MarketHeatmapProps {
  onAskAgent?: (prompt: string) => void;
}

const Sparkline24h: React.FC<{ data?: number[]; isPositive: boolean; width?: number; height?: number }> = ({
  data,
  isPositive,
  width = 54,
  height = 20
}) => {
  const points = data && data.length > 1
    ? data
    : [100, 100.8, 99.5, 101.4, 100.9, isPositive ? 102.8 : 97.2];

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  const svgPoints = points.map((val, idx) => {
    const x = (idx / (points.length - 1)) * width;
    const y = height - ((val - min) / range) * (height - 6) - 3;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const strokeColor = isPositive ? '#10b981' : '#ef4444';
  const fillColor = isPositive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';

  const firstX = 0;
  const lastX = width;
  const bottomY = height;
  const areaPoints = `${firstX},${bottomY} ${svgPoints} ${lastX},${bottomY}`;

  return (
    <svg width={width} height={height} className="overflow-visible shrink-0 pointer-events-none">
      <polygon points={areaPoints} fill={fillColor} />
      <polyline
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={svgPoints}
      />
    </svg>
  );
};

export const MarketHeatmap: React.FC<MarketHeatmapProps> = ({ onAskAgent }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('ALL');
  const [colorMetric, setColorMetric] = useState<'changePct' | 'sentiment'>('changePct');
  const [viewMode, setViewMode] = useState<'treemap' | 'grid'>('treemap');
  const [selectedStock, setSelectedStock] = useState<HeatmapStockItem | null>(null);

  const [comparedSectors, setComparedSectors] = useState<string[]>([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState<boolean>(false);

  const [isMacroExpanded, setIsMacroExpanded] = useState<boolean>(true);
  const [macroTab, setMacroTab] = useState<'overview' | 'factors' | 'rationale' | 'opportunities'>('overview');

  const macroData = EXECUTIVE_MACRO_GEOPOLITICAL_STATUS;

  const toggleCompareSector = (sectorName: string) => {
    setComparedSectors(prev => {
      if (prev.includes(sectorName)) {
        return prev.filter(s => s !== sectorName);
      }
      if (prev.length >= 2) {
        return [prev[1], sectorName];
      }
      const newArr = [...prev, sectorName];
      if (newArr.length === 2) {
        setIsCompareModalOpen(true);
      }
      return newArr;
    });
  };

  const totalMarketCap = useMemo(() => {
    return PSX_HEATMAP_DATA.reduce((acc, sec) => acc + sec.totalMarketCapBillion, 0);
  }, []);

  const marketBreadth = useMemo(() => {
    let advancers = 0;
    let decliners = 0;
    let unchanged = 0;

    PSX_HEATMAP_DATA.forEach(sec => {
      sec.stocks.forEach(stk => {
        if (stk.changePct > 0) advancers++;
        else if (stk.changePct < 0) decliners++;
        else unchanged++;
      });
    });

    return { advancers, decliners, unchanged };
  }, []);

  const filteredSectors = useMemo(() => {
    return PSX_HEATMAP_DATA.map(sec => {
      if (selectedSector !== 'ALL' && sec.sector !== selectedSector) {
        return null;
      }

      const matchingStocks = sec.stocks.filter(stk => {
        const query = searchQuery.toLowerCase().trim();
        if (!query) return true;
        return (
          stk.ticker.toLowerCase().includes(query) ||
          stk.name.toLowerCase().includes(query) ||
          stk.sector.toLowerCase().includes(query)
        );
      });

      if (matchingStocks.length === 0) return null;

      return {
        ...sec,
        stocks: matchingStocks
      };
    }).filter(Boolean) as typeof PSX_HEATMAP_DATA;
  }, [searchQuery, selectedSector]);

  const isolatedSectorObj = useMemo(() => {
    if (selectedSector === 'ALL') return null;
    const secObj = PSX_HEATMAP_DATA.find(s => s.sector === selectedSector);
    if (!secObj) return null;

    const sortedByChange = [...secObj.stocks].sort((a, b) => b.changePct - a.changePct);
    const topGainer = sortedByChange[0];
    const topDecliner = sortedByChange[sortedByChange.length - 1];

    const validPeCount = secObj.stocks.filter(s => s.peRatio && s.peRatio > 0).length;
    const avgPe = validPeCount > 0
      ? (secObj.stocks.reduce((acc, s) => acc + (s.peRatio || 0), 0) / validPeCount).toFixed(1)
      : 'N/A';

    const avgYield = (secObj.stocks.reduce((acc, s) => acc + (s.dividendYieldPct || 0), 0) / secObj.stocks.length).toFixed(1);
    const capWeight = ((secObj.totalMarketCapBillion / totalMarketCap) * 100).toFixed(1);

    return {
      ...secObj,
      topGainer,
      topDecliner,
      avgPe,
      avgYield,
      capWeight
    };
  }, [selectedSector, totalMarketCap]);

  const getItemBackgroundColor = (item: HeatmapStockItem) => {
    if (colorMetric === 'changePct') {
      const val = item.changePct;
      if (val >= 3.0) return 'bg-[#059669] text-white hover:bg-[#047857] border-[#10b981]';
      if (val >= 1.5) return 'bg-[#10b981]/80 text-white hover:bg-[#10b981] border-[#34d399]';
      if (val > 0) return 'bg-[#064e3b] text-[#a7f3d0] hover:bg-[#047857] border-[#059669]';
      if (val === 0) return 'bg-[#27272a] text-[#a1a1aa] hover:bg-[#3f3f46] border-[#52525b]';
      if (val > -1.5) return 'bg-[#7f1d1d] text-[#fecaca] hover:bg-[#991b1b] border-[#dc2626]';
      if (val > -3.0) return 'bg-[#dc2626]/80 text-white hover:bg-[#dc2626] border-[#f87171]';
      return 'bg-[#b91c1c] text-white hover:bg-[#991b1b] border-[#ef4444]';
    } else {
      const score = item.sentimentScore;
      if (score >= 60) return 'bg-[#059669] text-white hover:bg-[#047857] border-[#10b981]';
      if (score >= 20) return 'bg-[#064e3b] text-[#a7f3d0] hover:bg-[#047857] border-[#059669]';
      if (score >= -20) return 'bg-[#27272a] text-[#a1a1aa] hover:bg-[#3f3f46] border-[#52525b]';
      if (score >= -60) return 'bg-[#7f1d1d] text-[#fecaca] hover:bg-[#991b1b] border-[#dc2626]';
      return 'bg-[#b91c1c] text-white hover:bg-[#991b1b] border-[#ef4444]';
    }
  };

  return (
    <div className="space-y-6 font-mono">

      {/* EXECUTIVE MACRO & GEOPOLITICAL STATUS */}
      <div className="bg-[#121214] border border-[#27272a] rounded-lg shadow-sm overflow-hidden">
        <div className="bg-[#18181b] p-4 border-b border-[#27272a] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-[#3b82f6]/10 border border-[#3b82f6]/30 rounded-lg text-[#3b82f6]">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] bg-[#3b82f6] text-white px-2 py-0.5 rounded font-extrabold uppercase tracking-wider">
                  PSX MACRO INTELLIGENCE
                </span>
                <span className="text-[10px] text-[#10b981] font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse"></span>
                  {macroData.lastUpdated}
                </span>
              </div>
              <h2 className="text-base sm:text-lg font-bold text-[#fafafa] mt-0.5">
                Executive Macro, Geopolitical & Market Risk Matrix
              </h2>
            </div>
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto justify-between sm:justify-end">
            <div className="px-3 py-1 bg-[#10b981]/15 border border-[#10b981]/30 rounded text-xs font-bold text-[#10b981] flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>MARKET RISK: {macroData.overallMarketRisk.score}/10 ({macroData.overallMarketRisk.rating})</span>
            </div>

            <button
              onClick={() => setIsMacroExpanded(!isMacroExpanded)}
              className="px-2.5 py-1 bg-[#27272a] hover:bg-[#3f3f46] text-[#fafafa] rounded text-xs font-bold flex items-center space-x-1 transition-all"
            >
              <span>{isMacroExpanded ? 'Hide Briefing' : 'Show Briefing'}</span>
              {isMacroExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {isMacroExpanded && (
          <div className="p-4 space-y-5">

            <div className="flex items-center space-x-2 border-b border-[#27272a] pb-2 text-xs overflow-x-auto">
              {[
                { key: 'overview', icon: <PieChart className="w-3.5 h-3.5" />, label: 'Macro & Geopolitical Status' },
                { key: 'factors', icon: <BarChart3 className="w-3.5 h-3.5" />, label: 'Key Positive & Negative Factors' },
                { key: 'rationale', icon: <Info className="w-3.5 h-3.5" />, label: 'Executive Summary & Rationale' },
                { key: 'opportunities', icon: <Zap className="w-3.5 h-3.5" />, label: 'Tactical Market Opportunities' }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setMacroTab(tab.key as any)}
                  className={`px-3 py-1.5 rounded font-bold transition-all flex items-center space-x-1.5 whitespace-nowrap ${
                    macroTab === tab.key
                      ? tab.key === 'opportunities' ? 'bg-[#10b981] text-white shadow-xs' : 'bg-[#3b82f6] text-white shadow-xs'
                      : 'text-[#a1a1aa] hover:text-[#fafafa] bg-[#18181b]'
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {macroTab === 'overview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
                <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3.5 space-y-2">
                  <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                    <span className="text-[10px] text-[#3b82f6] font-bold flex items-center gap-1">
                      <TrendingUp className="w-3.5 h-3.5" />
                      MACROECONOMIC STATUS
                    </span>
                    <span className="px-2 py-0.5 bg-[#10b981]/15 text-[#10b981] rounded text-[10px] font-bold">
                      {macroData.macroEconomicStatus.level}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-[#fafafa]">{macroData.macroEconomicStatus.label}</h3>
                  <p className="text-[11px] text-[#a1a1aa] font-sans leading-relaxed">{macroData.macroEconomicStatus.description}</p>
                  <div className="pt-2 border-t border-[#27272a] space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">SBP Policy Rate:</span>
                      <span className="font-bold text-[#fafafa]">{macroData.macroEconomicStatus.policyRate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">CPI Inflation:</span>
                      <span className="font-bold text-[#10b981]">{macroData.macroEconomicStatus.cpiInflation}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">GDP Growth Target:</span>
                      <span className="font-bold text-[#fafafa]">{macroData.macroEconomicStatus.gdpGrowthProj}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3.5 space-y-2">
                  <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                    <span className="text-[10px] text-[#f59e0b] font-bold flex items-center gap-1">
                      <Globe className="w-3.5 h-3.5" />
                      GEOPOLITICAL STATUS
                    </span>
                    <span className="px-2 py-0.5 bg-[#f59e0b]/15 text-[#f59e0b] rounded text-[10px] font-bold">MODERATE FRICTION</span>
                  </div>
                  <h3 className="text-xs font-bold text-[#fafafa]">{macroData.geopoliticalStatus.label}</h3>
                  <p className="text-[11px] text-[#a1a1aa] font-sans leading-relaxed">{macroData.geopoliticalStatus.description}</p>
                  <div className="pt-2 border-t border-[#27272a] space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">Middle East Shipping:</span>
                      <span className="font-bold text-[#f59e0b]">{macroData.geopoliticalStatus.straitOfHormuz}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">Energy Impact:</span>
                      <span className="font-bold text-[#10b981]">Net Positive for Local E&P Revenues</span>
                    </div>
                  </div>
                </div>

                <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3.5 space-y-2">
                  <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                    <span className="text-[10px] text-[#10b981] font-bold flex items-center gap-1">
                      <Award className="w-3.5 h-3.5" />
                      IMF PROGRAM STATUS
                    </span>
                    <span className="px-2 py-0.5 bg-[#10b981]/15 text-[#10b981] rounded text-[10px] font-bold">{macroData.imfProgramStatus.status}</span>
                  </div>
                  <h3 className="text-xs font-bold text-[#fafafa]">{macroData.imfProgramStatus.facility}</h3>
                  <p className="text-[11px] text-[#a1a1aa] font-sans leading-relaxed">{macroData.imfProgramStatus.conditionalityCompliance}</p>
                  <div className="pt-2 border-t border-[#27272a] space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">Recent Disbursement:</span>
                      <span className="font-bold text-[#10b981]">{macroData.imfProgramStatus.trancheAmount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">Next Board Review:</span>
                      <span className="font-bold text-[#fafafa]">{macroData.imfProgramStatus.nextReviewDate}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3.5 space-y-2">
                  <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                    <span className="text-[10px] text-[#3b82f6] font-bold flex items-center gap-1">
                      <DollarSign className="w-3.5 h-3.5" />
                      CURRENCY STATUS (USD/PKR)
                    </span>
                    <span className="px-2 py-0.5 bg-[#3b82f6]/15 text-[#3b82f6] rounded text-[10px] font-bold">RANGE-BOUND</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-bold text-[#fafafa]">{macroData.currencyStatus.rate}</span>
                    <span className="text-[10px] text-[#10b981] font-bold">{macroData.currencyStatus.change1D}</span>
                  </div>
                  <div className="pt-2 border-t border-[#27272a] space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">SBP Net Reserves:</span>
                      <span className="font-bold text-[#10b981]">{macroData.currencyStatus.sbpReserveLevel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">Worker Remittances:</span>
                      <span className="font-bold text-[#fafafa]">{macroData.currencyStatus.remittanceTrend}</span>
                    </div>
                    <p className="text-[10px] text-[#a1a1aa] font-sans pt-1">Outlook: {macroData.currencyStatus.outlook}</p>
                  </div>
                </div>

                <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3.5 space-y-2 md:col-span-2 lg:col-span-2">
                  <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                    <span className="text-[10px] text-[#10b981] font-bold flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      SYSTEMIC PSX MARKET RISK ASSESSMENT
                    </span>
                    <span className="text-[10px] text-[#a1a1aa]">{macroData.overallMarketRisk.volatilityIndex}</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
                    <div>
                      <span className="text-[10px] text-[#a1a1aa] block">QUANT RISK SCORE</span>
                      <span className="text-2xl font-black text-[#10b981]">
                        {macroData.overallMarketRisk.score} <span className="text-xs font-normal text-[#a1a1aa]">/ 10</span>
                      </span>
                      <span className="text-[10px] text-[#10b981] font-bold block">{macroData.overallMarketRisk.rating}</span>
                    </div>
                    <div className="sm:col-span-2 space-y-1.5">
                      <div className="flex justify-between text-[10px] text-[#a1a1aa]">
                        <span>0 (Low Risk / Strong Bull)</span>
                        <span>5 (Neutral)</span>
                        <span>10 (High Crash Risk)</span>
                      </div>
                      <div className="h-3 bg-[#27272a] rounded-full overflow-hidden relative p-0.5 border border-[#3f3f46]">
                        <div
                          className="h-full bg-gradient-to-r from-[#10b981] via-[#f59e0b] to-[#ef4444] rounded-full"
                          style={{ width: `${(macroData.overallMarketRisk.score / 10) * 100}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-[#a1a1aa] font-sans leading-relaxed">
                        Low systemic risk score driven by massive rate cuts, single-digit CPI inflation (6.2%), and structural circular debt settlements.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {macroTab === 'factors' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="bg-[#18181b] border border-[#10b981]/30 rounded-lg p-4 space-y-3">
                  <div className="flex items-center space-x-2 border-b border-[#27272a] pb-2 text-[#10b981]">
                    <CheckCircle2 className="w-4 h-4" />
                    <h3 className="font-bold text-sm uppercase tracking-wide">Key Positive Catalysts (Bullish Drivers)</h3>
                  </div>
                  <div className="space-y-3">
                    {macroData.keyPositiveFactors.map((pos) => (
                      <div key={pos.id} className="bg-[#121214] p-3 rounded border border-[#27272a] space-y-1 hover:border-[#10b981]/50 transition-all">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-[#fafafa] text-xs">{pos.title}</span>
                          <span className="text-[9px] px-1.5 py-0.5 bg-[#10b981]/15 text-[#10b981] rounded font-bold">{pos.impactSector}</span>
                        </div>
                        <p className="text-[11px] text-[#a1a1aa] font-sans leading-relaxed">{pos.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-[#18181b] border border-[#ef4444]/30 rounded-lg p-4 space-y-3">
                  <div className="flex items-center space-x-2 border-b border-[#27272a] pb-2 text-[#ef4444]">
                    <AlertTriangle className="w-4 h-4" />
                    <h3 className="font-bold text-sm uppercase tracking-wide">Key Negative Factors & Headwinds</h3>
                  </div>
                  <div className="space-y-3">
                    {macroData.keyNegativeFactors.map((neg) => (
                      <div key={neg.id} className="bg-[#121214] p-3 rounded border border-[#27272a] space-y-1 hover:border-[#ef4444]/50 transition-all">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-[#fafafa] text-xs">{neg.title}</span>
                          <span className="text-[9px] px-1.5 py-0.5 bg-[#ef4444]/15 text-[#ef4444] rounded font-bold">{neg.impactSector}</span>
                        </div>
                        <p className="text-[11px] text-[#a1a1aa] font-sans leading-relaxed">{neg.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {macroTab === 'rationale' && (
              <div className="bg-[#18181b] border border-[#3b82f6]/30 rounded-lg p-5 space-y-4 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-[#27272a] pb-3">
                  <div className="flex items-center space-x-2 text-[#3b82f6]">
                    <Bot className="w-5 h-5" />
                    <h3 className="font-bold text-sm sm:text-base text-[#fafafa]">{macroData.executiveSummary.headline}</h3>
                  </div>
                  <span className="px-2.5 py-1 bg-[#3b82f6]/10 text-[#3b82f6] rounded border border-[#3b82f6]/30 font-bold text-[10px]">
                    TERMINAL MACRO SYNTHESIS
                  </span>
                </div>
                <div className="bg-[#121214] p-4 rounded border border-[#27272a] whitespace-pre-line font-sans text-xs text-[#d4d4d8] leading-relaxed">
                  {macroData.executiveSummary.rationaleText}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  <div className="p-3 bg-[#10b981]/10 border border-[#10b981]/30 rounded space-y-1">
                    <span className="text-[10px] text-[#10b981] font-bold uppercase block">BULL CASE CATALYST</span>
                    <p className="text-xs text-[#fafafa] font-sans">{macroData.executiveSummary.bullCaseDriver}</p>
                  </div>
                  <div className="p-3 bg-[#ef4444]/10 border border-[#ef4444]/30 rounded space-y-1">
                    <span className="text-[10px] text-[#ef4444] font-bold uppercase block">BEAR CASE TAIL RISK</span>
                    <p className="text-xs text-[#fafafa] font-sans">{macroData.executiveSummary.bearCaseRisk}</p>
                  </div>
                </div>
              </div>
            )}

            {macroTab === 'opportunities' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                  <span className="text-xs font-bold text-[#fafafa] flex items-center gap-1.5">
                    <Zap className="w-4 h-4 text-[#10b981]" />
                    HIGH-CONVICTION QUANT MARKET OPPORTUNITIES IN THIS REGIME
                  </span>
                  <span className="text-[10px] text-[#a1a1aa]">4 Tactical Plays Active</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {macroData.tacticalOpportunities.map((opp) => (
                    <div
                      key={opp.id}
                      className="bg-[#18181b] border border-[#27272a] hover:border-[#10b981]/60 rounded-lg p-4 space-y-3 transition-all shadow-xs flex flex-col justify-between"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="px-2 py-0.5 bg-[#10b981]/15 text-[#10b981] rounded font-bold text-[10px] tracking-wider uppercase">
                            {opp.strategyType.replace('_', ' ')}
                          </span>
                          <div className="flex items-center space-x-2 text-[10px] text-[#a1a1aa]">
                            <span>Horizon: <strong className="text-[#fafafa]">{opp.targetHorizon}</strong></span>
                            <span>•</span>
                            <span>R:R <strong className="text-[#10b981]">{opp.riskRewardRatio}</strong></span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <h4 className="font-bold text-sm text-[#fafafa]">{opp.sector}</h4>
                          <div className="flex items-center space-x-1">
                            {opp.tickers.map((t) => (
                              <span key={t} className="px-1.5 py-0.5 bg-[#3b82f6]/15 text-[#3b82f6] border border-[#3b82f6]/30 rounded font-bold text-[10px]">
                                ${t}
                              </span>
                            ))}
                          </div>
                        </div>
                        <p className="text-xs text-[#a1a1aa] font-sans leading-relaxed">{opp.thesis}</p>
                      </div>
                      <button
                        onClick={() => {
                          if (onAskAgent) {
                            onAskAgent(`Tell me more about the high-conviction trade thesis for ${opp.sector} (${opp.tickers.join(', ')}). What are the exact price targets and execution triggers?`);
                          }
                        }}
                        className="w-full py-1.5 bg-[#27272a] hover:bg-[#3b82f6] text-[#fafafa] font-mono text-[11px] font-bold rounded transition-all flex items-center justify-center space-x-1.5"
                      >
                        <Bot className="w-3.5 h-3.5" />
                        <span>Ask Agent to Backtest ${opp.tickers[0]} Trade</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
      </div>

      {/* HEATMAP HEADER & TOOLBAR */}
      <div className="bg-[#121214] border border-[#27272a] rounded-lg p-4 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#3b82f6] text-xs font-bold uppercase tracking-wider mb-1">
              <Grid className="w-4 h-4 text-[#3b82f6]" />
              <span>PSX REAL-TIME MARKET HEATMAP & CAPITALIZATION MATRIX</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-[#fafafa]">PSX Sector Performance Treemap</h2>
            <p className="text-xs text-[#a1a1aa] font-sans mt-0.5 max-w-2xl">
              Visualizing relative market capitalization weights and real-time intraday price deltas across key PSX benchmark equities.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <div className="flex items-center space-x-1 bg-[#18181b] p-1 rounded-md border border-[#27272a] text-xs">
              <button onClick={() => setColorMetric('changePct')} className={`px-3 py-1 rounded transition-all ${colorMetric === 'changePct' ? 'bg-[#27272a] text-[#fafafa] font-bold border border-[#3f3f46]' : 'text-[#a1a1aa] hover:text-[#fafafa]'}`}>Price Change %</button>
              <button onClick={() => setColorMetric('sentiment')} className={`px-3 py-1 rounded transition-all ${colorMetric === 'sentiment' ? 'bg-[#27272a] text-[#fafafa] font-bold border border-[#3f3f46]' : 'text-[#a1a1aa] hover:text-[#fafafa]'}`}>AI Sentiment</button>
            </div>
            <div className="flex items-center space-x-1 bg-[#18181b] p-1 rounded-md border border-[#27272a] text-xs">
              <button onClick={() => setViewMode('treemap')} className={`px-3 py-1 rounded transition-all flex items-center space-x-1 ${viewMode === 'treemap' ? 'bg-[#3b82f6] text-white font-bold' : 'text-[#a1a1aa] hover:text-[#fafafa]'}`}><Grid className="w-3.5 h-3.5" /><span>Treemap</span></button>
              <button onClick={() => setViewMode('grid')} className={`px-3 py-1 rounded transition-all flex items-center space-x-1 ${viewMode === 'grid' ? 'bg-[#3b82f6] text-white font-bold' : 'text-[#a1a1aa] hover:text-[#fafafa]'}`}><Layers className="w-3.5 h-3.5" /><span>Sector Cards</span></button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 pt-3 border-t border-[#27272a] text-xs">
          <div className="bg-[#18181b] p-2.5 rounded border border-[#27272a]">
            <span className="text-[10px] text-[#a1a1aa] block">TOTAL MARKET CAP</span>
            <span className="text-[#fafafa] font-bold text-sm">PKR {totalMarketCap.toLocaleString()} Billion</span>
          </div>
          <div className="bg-[#18181b] p-2.5 rounded border border-[#27272a]">
            <span className="text-[10px] text-[#a1a1aa] block">BENCHMARK KSE-100</span>
            <span className="text-[#10b981] font-bold text-sm flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5" />114,850.40 (+0.54%)</span>
          </div>
          <div className="bg-[#18181b] p-2.5 rounded border border-[#27272a]">
            <span className="text-[10px] text-[#a1a1aa] block">MARKET BREADTH</span>
            <div className="flex items-center space-x-2 text-xs font-bold mt-0.5">
              <span className="text-[#10b981]">{marketBreadth.advancers} Adv</span>
              <span className="text-[#a1a1aa]">•</span>
              <span className="text-[#ef4444]">{marketBreadth.decliners} Dec</span>
              <span className="text-[#a1a1aa]">•</span>
              <span className="text-[#a1a1aa]">{marketBreadth.unchanged} Unch</span>
            </div>
          </div>
          <div className="bg-[#18181b] p-2.5 rounded border border-[#27272a]">
            <span className="text-[10px] text-[#a1a1aa] block">TOP SECTOR GAINER</span>
            <span className="text-[#10b981] font-bold text-sm">Power Gen (+2.58%)</span>
          </div>
          <div className="hidden lg:block bg-[#18181b] p-2.5 rounded border border-[#27272a]">
            <span className="text-[10px] text-[#a1a1aa] block">QUANT COVERAGE</span>
            <span className="text-[#3b82f6] font-bold text-sm flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5 text-[#10b981]" />Real-time Feed</span>
          </div>
        </div>

        <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 text-xs">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2.5 w-full lg:w-auto">
            <div className="flex items-center space-x-1.5 text-xs text-[#3b82f6] font-bold shrink-0">
              <Filter className="w-4 h-4 text-[#3b82f6]" />
              <span>ISOLATE SECTOR:</span>
            </div>
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="bg-[#121214] text-[#fafafa] border border-[#3b82f6]/60 rounded-md px-3 py-2 text-xs font-mono font-bold focus:outline-none focus:border-[#3b82f6] cursor-pointer hover:bg-[#27272a] transition-all w-full sm:w-72"
            >
              <option value="ALL">All PSX Sectors (Full Market Heatmap)</option>
              {PSX_HEATMAP_DATA.map(sec => (
                <option key={sec.sector} value={sec.sector}>
                  {sec.sector} ({sec.avgChangePct > 0 ? '+' : ''}{sec.avgChangePct}%)
                </option>
              ))}
            </select>
            {selectedSector !== 'ALL' && (
              <button onClick={() => setSelectedSector('ALL')} className="px-2.5 py-1.5 bg-[#27272a] hover:bg-[#3f3f46] text-[#a1a1aa] hover:text-[#fafafa] rounded text-xs flex items-center space-x-1 transition-all shrink-0">
                <X className="w-3.5 h-3.5" /><span>Reset Sector</span>
              </button>
            )}
          </div>

          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 lg:pb-0">
            <button onClick={() => setSelectedSector('ALL')} className={`px-2.5 py-1 rounded text-[11px] font-mono font-medium transition-all whitespace-nowrap ${selectedSector === 'ALL' ? 'bg-[#3b82f6] text-white font-bold' : 'bg-[#121214] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'}`}>All</button>
            {PSX_HEATMAP_DATA.map(sec => (
              <button key={sec.sector} onClick={() => setSelectedSector(sec.sector)} className={`px-2.5 py-1 rounded text-[11px] font-mono font-medium transition-all whitespace-nowrap ${selectedSector === sec.sector ? 'bg-[#27272a] text-[#fafafa] border border-[#3f3f46] font-bold' : 'bg-[#121214] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'}`}>{sec.sector}</button>
            ))}
          </div>

          <div className="relative w-full lg:w-60 shrink-0">
            <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-[#a1a1aa]" />
            <input
              type="text"
              placeholder="Search $OGDC, $SYS..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#121214] border border-[#27272a] rounded pl-8 pr-3 py-1.5 text-xs text-[#fafafa] placeholder-[#a1a1aa] focus:outline-none focus:border-[#3b82f6]"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-2 top-2 text-[#a1a1aa] hover:text-[#fafafa]">×</button>
            )}
          </div>
        </div>
      </div>

      {isolatedSectorObj && (
        <div className="bg-[#121214] border border-[#3b82f6]/40 rounded-lg p-4 space-y-3 font-mono text-xs shadow-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#27272a] pb-3">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 bg-[#3b82f6] text-white rounded font-extrabold text-[10px] tracking-wider uppercase">ISOLATED SECTOR ANALYSIS</span>
              <h3 className="text-base sm:text-lg font-bold text-[#fafafa]">{isolatedSectorObj.sector}</h3>
            </div>
            <span className={`text-sm font-extrabold px-3 py-1 rounded ${isolatedSectorObj.avgChangePct >= 0 ? 'bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30' : 'bg-[#ef4444]/15 text-[#ef4444] border border-[#ef4444]/30'}`}>
              Sector Avg: {isolatedSectorObj.avgChangePct > 0 ? `+${isolatedSectorObj.avgChangePct}%` : `${isolatedSectorObj.avgChangePct}%`}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-[#18181b] p-3 rounded border border-[#27272a]">
              <span className="text-[10px] text-[#a1a1aa] block">TOTAL SECTOR MARKET CAP</span>
              <span className="text-sm font-bold text-[#fafafa]">PKR {isolatedSectorObj.totalMarketCapBillion}B ({isolatedSectorObj.capWeight}% weight)</span>
            </div>
            <div className="bg-[#18181b] p-3 rounded border border-[#27272a]">
              <span className="text-[10px] text-[#a1a1aa] block">CONSTITUENT STOCKS</span>
              <span className="text-sm font-bold text-[#fafafa]">{isolatedSectorObj.stocks.length} Equities</span>
            </div>
            <div className="bg-[#18181b] p-3 rounded border border-[#27272a]">
              <span className="text-[10px] text-[#a1a1aa] block">SECTOR AVG P/E</span>
              <span className="text-sm font-bold text-[#3b82f6]">{isolatedSectorObj.avgPe}x</span>
            </div>
            <div className="bg-[#18181b] p-3 rounded border border-[#27272a]">
              <span className="text-[10px] text-[#a1a1aa] block">SECTOR AVG DIV YIELD</span>
              <span className="text-sm font-bold text-[#10b981]">{isolatedSectorObj.avgYield}%</span>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {isolatedSectorObj.topGainer && (
              <div className="flex items-center justify-between p-2.5 bg-[#18181b] rounded border border-[#27272a]">
                <div className="flex items-center space-x-2"><TrendingUp className="w-4 h-4 text-[#10b981]" /><span className="text-[11px] text-[#a1a1aa]">Sector Top Gainer:</span><span className="font-bold text-[#fafafa]">${isolatedSectorObj.topGainer.ticker}</span></div>
                <span className="font-bold text-[#10b981]">+{isolatedSectorObj.topGainer.changePct}% (PKR {isolatedSectorObj.topGainer.price.toFixed(2)})</span>
              </div>
            )}
            {isolatedSectorObj.topDecliner && (
              <div className="flex items-center justify-between p-2.5 bg-[#18181b] rounded border border-[#27272a]">
                <div className="flex items-center space-x-2"><TrendingDown className="w-4 h-4 text-[#ef4444]" /><span className="text-[11px] text-[#a1a1aa]">Sector Top Lag:</span><span className="font-bold text-[#fafafa]">${isolatedSectorObj.topDecliner.ticker}</span></div>
                <span className="font-bold text-[#ef4444]">{isolatedSectorObj.topDecliner.changePct}% (PKR {isolatedSectorObj.topDecliner.price.toFixed(2)})</span>
              </div>
            )}
          </div>
        </div>
      )}

      {comparedSectors.length > 0 && (
        <div className="bg-[#18181b] border-2 border-[#3b82f6] p-3 rounded-lg flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xl">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 bg-[#3b82f6]/20 text-[#3b82f6] rounded"><GitCompare className="w-4 h-4" /></div>
            <div>
              <span className="text-xs font-bold text-[#fafafa] block">SECTOR COMPARISON ACTIVE ({comparedSectors.length}/2 Selected)</span>
              <div className="flex items-center space-x-2 mt-0.5">
                {comparedSectors.map(sec => (
                  <span key={sec} className="text-[10px] bg-[#3b82f6]/15 text-[#3b82f6] border border-[#3b82f6]/30 px-2 py-0.5 rounded font-bold">{sec}</span>
                ))}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
            <button onClick={() => { if (comparedSectors.length < 2) { const other = PSX_HEATMAP_DATA.find(s => s.sector !== comparedSectors[0]); if (other) setComparedSectors([comparedSectors[0], other.sector]); } setIsCompareModalOpen(true); }} className="px-3 py-1.5 bg-[#3b82f6] hover:bg-blue-600 text-white font-mono font-bold text-xs rounded transition-all flex items-center space-x-1.5 cursor-pointer shadow-md">
              <BarChart2 className="w-4 h-4" /><span>Launch Side-by-Side Comparison Chart</span>
            </button>
            <button onClick={() => setComparedSectors([])} className="p-1.5 bg-[#27272a] hover:bg-[#3f3f46] text-[#a1a1aa] hover:text-[#fafafa] rounded transition-all"><X className="w-4 h-4" /></button>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-[#121214] border border-[#27272a] px-4 py-2.5 rounded-lg text-[11px] text-[#a1a1aa] gap-2">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-[#10b981] animate-ping" />
          <span className="font-bold text-[#fafafa]">LIVE TICKER FEED & PULSE ANIMATIONS ACTIVE</span>
          <span className="text-[10px] bg-[#10b981]/15 text-[#10b981] px-2 py-0.5 rounded border border-[#10b981]/30 font-bold">Real-Time PSX Feed</span>
        </div>
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-[#fafafa] hidden md:inline">{colorMetric === 'changePct' ? '1D PRICE CHANGE SCALE:' : 'AI SENTIMENT SCORE SCALE:'}</span>
          <div className="flex items-center space-x-1 font-mono">
            <span className="px-2 py-0.5 rounded bg-[#b91c1c] text-white">-3.0%+</span>
            <span className="px-2 py-0.5 rounded bg-[#7f1d1d] text-[#fecaca]">-1.5%</span>
            <span className="px-2 py-0.5 rounded bg-[#27272a] text-[#a1a1aa]">0.0%</span>
            <span className="px-2 py-0.5 rounded bg-[#064e3b] text-[#a7f3d0]">+1.5%</span>
            <span className="px-2 py-0.5 rounded bg-[#059669] text-white">+3.0%+</span>
          </div>
        </div>
      </div>

      {viewMode === 'treemap' ? (
        <div className="space-y-6">
          {filteredSectors.map(sec => {
            const sectorCapWeightPct = ((sec.totalMarketCapBillion / totalMarketCap) * 100).toFixed(1);
            const isComparing = comparedSectors.includes(sec.sector);
            return (
              <div key={sec.sector} className={`bg-[#121214] border ${isComparing ? 'border-[#3b82f6] shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 'border-[#27272a]'} hover:border-[#3b82f6] transition-all duration-300 rounded-lg p-4 space-y-3`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#27272a] pb-2 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-[#fafafa] text-sm font-mono">{sec.sector}</span>
                    <span className="text-[10px] text-[#a1a1aa] bg-[#18181b] px-2 py-0.5 rounded border border-[#27272a]">Market Cap: PKR {sec.totalMarketCapBillion}B ({sectorCapWeightPct}%)</span>
                  </div>
                  <div className="flex items-center space-x-2 sm:space-x-3">
                    <span className={`font-mono font-bold text-xs ${sec.avgChangePct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                      Sector Avg: {sec.avgChangePct > 0 ? `+${sec.avgChangePct}%` : `${sec.avgChangePct}%`}
                    </span>
                    <button onClick={() => toggleCompareSector(sec.sector)} className={`px-2.5 py-1 rounded font-mono font-bold text-[10px] flex items-center space-x-1 transition-all border ${isComparing ? 'bg-[#3b82f6] text-white border-[#3b82f6]' : 'bg-[#27272a] hover:bg-[#3f3f46] text-[#fafafa] border-[#3f3f46]'}`}>
                      <GitCompare className="w-3 h-3" /><span>{isComparing ? 'Comparing' : '+ Compare'}</span>
                    </button>
                    <button onClick={() => { if (onAskAgent) onAskAgent(`QuantAgent, analyze current macro drivers and news sentiment for the ${sec.sector} sector. What are the top actionable trade opportunities and catalyst triggers right now?`); }} className="px-2.5 py-1 bg-[#10b981]/15 hover:bg-[#10b981]/25 text-[#10b981] border border-[#10b981]/40 rounded font-mono font-bold text-[10px] flex items-center space-x-1 transition-all">
                      <Zap className="w-3 h-3 text-[#10b981]" /><span>Show Opportunity</span>
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-12 gap-2.5 min-h-[140px]">
                  {sec.stocks.map(stk => {
                    const stockWeightPct = (stk.marketCapBillion / sec.totalMarketCapBillion) * 100;
                    let colSpan = 'col-span-6 sm:col-span-3';
                    if (stockWeightPct > 35) colSpan = 'col-span-12 sm:col-span-6 md:col-span-5';
                    else if (stockWeightPct > 20) colSpan = 'col-span-12 sm:col-span-6 md:col-span-4';
                    else if (stockWeightPct > 12) colSpan = 'col-span-6 sm:col-span-4 md:col-span-3';
                    const tileColor = getItemBackgroundColor(stk);
                    const glowClass = stk.changePct >= 0 ? 'hover:shadow-[0_0_18px_rgba(16,185,129,0.5)] hover:border-[#10b981]' : 'hover:shadow-[0_0_18px_rgba(239,68,68,0.5)] hover:border-[#ef4444]';
                    return (
                      <div key={stk.ticker} onClick={() => setSelectedStock(stk)} className={`${colSpan} ${tileColor} ${glowClass} border rounded-lg p-3 cursor-pointer transition-all duration-300 transform hover:scale-[1.02] hover:z-20 flex flex-col justify-between group relative min-h-[100px]`}>
                        <div className="flex items-start justify-between">
                          <div>
                            <span className="font-mono font-extrabold text-sm sm:text-base tracking-wide block">${stk.ticker}</span>
                            <span className="text-[10px] opacity-80 truncate block max-w-[130px] font-sans">{stk.name}</span>
                          </div>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 bg-black/40 rounded font-bold backdrop-blur-xs">
                            {colorMetric === 'changePct' ? `${stk.changePct > 0 ? '+' : ''}${stk.changePct}%` : `${stk.sentimentScore > 0 ? '+' : ''}${stk.sentimentScore}`}
                          </span>
                        </div>
                        <div className="my-1 flex items-center justify-between">
                          <span className="text-[11px] font-bold font-mono">PKR {stk.price.toFixed(2)}</span>
                          <Sparkline24h data={stk.sparkline24h} isPositive={stk.changePct >= 0} width={48} height={18} />
                        </div>
                        <div className="flex items-center justify-between pt-1 border-t border-white/10 font-mono text-[9px] opacity-75">
                          <span>MCap: {stk.marketCapBillion}B</span>
                          <span>Vol: {stk.volume}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSectors.map(sec => {
            const isComparing = comparedSectors.includes(sec.sector);
            return (
              <div key={sec.sector} className={`bg-[#121214] border ${isComparing ? 'border-[#3b82f6] shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 'border-[#27272a]'} hover:border-[#3b82f6] transition-all duration-300 transform hover:scale-[1.02] hover:z-10 rounded-lg p-4 space-y-3`}>
                <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-bold text-[#fafafa] text-sm">{sec.sector}</h3>
                    <Sparkline24h isPositive={sec.avgChangePct >= 0} width={40} height={16} />
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs font-bold font-mono ${sec.avgChangePct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                      {sec.avgChangePct > 0 ? `+${sec.avgChangePct}%` : `${sec.avgChangePct}%`}
                    </span>
                    <button onClick={() => toggleCompareSector(sec.sector)} className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all ${isComparing ? 'bg-[#3b82f6] text-white border-[#3b82f6]' : 'bg-[#27272a] text-[#a1a1aa] border-[#3f3f46]'}`}>
                      {isComparing ? 'Comparing' : '+ Compare'}
                    </button>
                    <button onClick={() => { if (onAskAgent) onAskAgent(`QuantAgent, analyze macro drivers and news sentiment for the ${sec.sector} sector. What are the top trade opportunities right now?`); }} className="px-2 py-0.5 bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30 rounded text-[10px] font-bold flex items-center gap-1">
                      <Zap className="w-3 h-3" /><span>Opportunity</span>
                    </button>
                  </div>
                </div>
                <div className="text-xs text-[#a1a1aa] flex justify-between font-mono">
                  <span>Total MCap: PKR {sec.totalMarketCapBillion}B</span>
                  <span>{sec.stocks.length} Equities</span>
                </div>
                <div className="space-y-1.5 pt-1">
                  {sec.stocks.map(stk => (
                    <div key={stk.ticker} onClick={() => setSelectedStock(stk)} className="flex items-center justify-between p-2 bg-[#18181b] hover:bg-[#27272a] rounded border border-[#27272a] cursor-pointer text-xs font-mono transition-all hover:scale-[1.01]">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-[#3b82f6]">${stk.ticker}</span>
                        <span className="text-[10px] text-[#a1a1aa] hidden sm:inline">{stk.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[#fafafa]">PKR {stk.price.toFixed(2)}</span>
                        <span className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${stk.changePct >= 0 ? 'bg-[#10b981]/15 text-[#10b981]' : 'bg-[#ef4444]/15 text-[#ef4444]'}`}>
                          {stk.changePct > 0 ? `+${stk.changePct}%` : `${stk.changePct}%`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedStock && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121214] border border-[#27272a] rounded-lg max-w-lg w-full p-6 space-y-5 shadow-2xl relative font-mono text-xs">
            <button onClick={() => setSelectedStock(null)} className="absolute top-4 right-4 text-[#a1a1aa] hover:text-[#fafafa] p-1 rounded-full hover:bg-[#27272a]">
              <X className="w-5 h-5" />
            </button>
            <div className="space-y-1">
              <div className="flex items-center justify-between pr-8">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/30 rounded font-bold text-xs">${selectedStock.ticker}</span>
                  <span className="text-xs text-[#a1a1aa]">{selectedStock.sector}</span>
                </div>
                <Sparkline24h data={selectedStock.sparkline24h} isPositive={selectedStock.changePct >= 0} width={64} height={24} />
              </div>
              <h3 className="text-xl font-bold text-[#fafafa] font-sans">{selectedStock.name}</h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-[#18181b] p-3 rounded-md border border-[#27272a]">
              <div><span className="text-[10px] text-[#a1a1aa] block">CURRENT PRICE</span><span className="text-base font-bold text-[#fafafa]">PKR {selectedStock.price.toFixed(2)}</span></div>
              <div><span className="text-[10px] text-[#a1a1aa] block">1D CHANGE</span><span className={`text-base font-bold flex items-center gap-0.5 ${selectedStock.changePct >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>{selectedStock.changePct >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}{selectedStock.changePct > 0 ? `+${selectedStock.changePct}%` : `${selectedStock.changePct}%`}</span></div>
              <div><span className="text-[10px] text-[#a1a1aa] block">MARKET CAP</span><span className="text-base font-bold text-[#fafafa]">PKR {selectedStock.marketCapBillion}B</span></div>
            </div>
            <div className="bg-[#18181b] border-l-4 border-[#10b981] p-3 rounded-r-md border-y border-r border-[#27272a] space-y-2">
              <span className="text-[10px] font-bold text-[#10b981] uppercase tracking-wider block flex items-center gap-1.5"><Gauge className="w-3.5 h-3.5 text-[#10b981]" />SECTOR & STOCK QUANT QUICK-STATS ROW</span>
              <div className="grid grid-cols-3 gap-2 text-center font-mono">
                <div className="bg-[#121214] p-2 rounded border border-[#27272a]"><span className="text-[9px] text-[#a1a1aa] block">SECTOR P/E RATIO</span><span className="text-sm font-extrabold text-[#fafafa]">{selectedStock.peRatio ? `${selectedStock.peRatio}x` : '4.8x'}</span></div>
                <div className="bg-[#121214] p-2 rounded border border-[#27272a]"><span className="text-[9px] text-[#a1a1aa] block">DIVIDEND YIELD</span><span className="text-sm font-extrabold text-[#10b981]">{selectedStock.dividendYieldPct ? `${selectedStock.dividendYieldPct}%` : '14.2%'}</span></div>
                <div className="bg-[#121214] p-2 rounded border border-[#27272a]"><span className="text-[9px] text-[#a1a1aa] block">30D VOLATILITY</span><span className="text-sm font-extrabold text-[#3b82f6]">{selectedStock.volatility30d ? `${selectedStock.volatility30d}%` : '14.5%'}</span></div>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[10px] text-[#a1a1aa]"><span>52W Low: PKR {selectedStock.low52}</span><span>52W High: PKR {selectedStock.high52}</span></div>
              <div className="h-2 bg-[#27272a] rounded-full overflow-hidden relative">
                <div className="h-full bg-[#3b82f6] rounded-full" style={{ width: `${Math.min(100, Math.max(10, ((selectedStock.price - selectedStock.low52) / (selectedStock.high52 - selectedStock.low52)) * 100))}%` }} />
              </div>
            </div>
            <div className="bg-[#18181b] border border-[#27272a] rounded p-3 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-[#3b82f6] flex items-center gap-1"><Sparkles className="w-3.5 h-3.5 text-[#3b82f6]" />AI QUANT SENTIMENT SCORE</span>
                <span className={`font-bold px-2 py-0.5 rounded text-[10px] ${selectedStock.sentimentScore >= 20 ? 'bg-[#10b981]/15 text-[#10b981]' : 'bg-[#ef4444]/15 text-[#ef4444]'}`}>
                  {selectedStock.sentimentScore > 0 ? `+${selectedStock.sentimentScore}` : selectedStock.sentimentScore} {selectedStock.sentiment}
                </span>
              </div>
              <p className="text-[11px] text-[#a1a1aa] font-sans leading-relaxed">{selectedStock.topDriver}</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-[#27272a]">
              <button onClick={() => { const p = `QuantAgent, based on ${selectedStock.sector} sector's current macro conditions and news sentiment for $${selectedStock.ticker} (${selectedStock.name}), what are the actionable trade opportunities, target entry prices, stop losses, and expected return horizon?`; setSelectedStock(null); if (onAskAgent) onAskAgent(p); }} className="py-2.5 bg-[#10b981] hover:bg-[#059669] text-white font-mono font-bold text-xs rounded transition-all flex items-center justify-center space-x-2 shadow-xs cursor-pointer"><Zap className="w-4 h-4 text-white" /><span>Show Opportunity</span></button>
              <button onClick={() => { const p = `Analyze $${selectedStock.ticker} (${selectedStock.name}) in detail. What is the projected impact of recent macro news, valuation multiples, and target buy/sell range?`; setSelectedStock(null); if (onAskAgent) onAskAgent(p); }} className="py-2.5 bg-[#3b82f6] hover:bg-blue-600 text-white font-mono font-bold text-xs rounded transition-all flex items-center justify-center space-x-2 shadow-xs cursor-pointer"><Bot className="w-4 h-4" /><span>Ask QuantAgent</span></button>
            </div>
          </div>
        </div>
      )}

      {isCompareModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121214] border border-[#27272a] rounded-lg max-w-3xl w-full p-6 space-y-6 shadow-2xl relative font-mono text-xs max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-[#27272a] pb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-[#3b82f6]/10 border border-[#3b82f6]/30 text-[#3b82f6] rounded-lg"><GitCompare className="w-5 h-5" /></div>
                <div>
                  <h3 className="text-base font-bold text-[#fafafa]">PSX Sector Side-by-Side Performance Comparison</h3>
                  <p className="text-[11px] text-[#a1a1aa]">Comparative 24-Hour intraday performance trajectory & quant valuation metrics</p>
                </div>
              </div>
              <button onClick={() => setIsCompareModalOpen(false)} className="text-[#a1a1aa] hover:text-[#fafafa] p-1.5 rounded-full hover:bg-[#27272a]"><X className="w-5 h-5" /></button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-[#18181b] p-3.5 rounded-lg border border-[#27272a]">
              <div>
                <label className="text-[10px] text-[#3b82f6] font-bold block mb-1">SECTOR A (PRIMARY)</label>
                <select value={comparedSectors[0] || PSX_HEATMAP_DATA[0].sector} onChange={(e) => setComparedSectors([e.target.value, comparedSectors[1] || PSX_HEATMAP_DATA[1].sector])} className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-3 py-1.5 text-xs font-mono focus:border-[#3b82f6] outline-none">
                  {PSX_HEATMAP_DATA.map(s => <option key={s.sector} value={s.sector}>{s.sector}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-[#10b981] font-bold block mb-1">SECTOR B (BENCHMARK)</label>
                <select value={comparedSectors[1] || PSX_HEATMAP_DATA[1].sector} onChange={(e) => setComparedSectors([comparedSectors[0] || PSX_HEATMAP_DATA[0].sector, e.target.value])} className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-3 py-1.5 text-xs font-mono focus:border-[#10b981] outline-none">
                  {PSX_HEATMAP_DATA.map(s => <option key={s.sector} value={s.sector}>{s.sector}</option>)}
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-[#fafafa] flex items-center gap-1.5"><Activity className="w-4 h-4 text-[#3b82f6]" />24-HOUR INTRADAY PERFORMANCE TRAJECTORY (%)</span>
                <span className="text-[10px] text-[#a1a1aa]">Real-Time PSX Feed</span>
              </div>
              <div className="h-60 bg-[#18181b] border border-[#27272a] rounded-lg p-3">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={(() => {
                    const secA = PSX_HEATMAP_DATA.find(s => s.sector === (comparedSectors[0] || PSX_HEATMAP_DATA[0].sector));
                    const secB = PSX_HEATMAP_DATA.find(s => s.sector === (comparedSectors[1] || PSX_HEATMAP_DATA[1].sector));
                    const changeA = secA ? secA.avgChangePct : 1.5;
                    const changeB = secB ? secB.avgChangePct : -0.8;
                    const times = ['09:30', '10:30', '11:30', '12:30', '13:30', '14:30', '15:30'];
                    return times.map((t, i) => {
                      const factor = i / (times.length - 1);
                      return {
                        time: t,
                        [secA ? secA.sector : 'Sector A']: +(changeA * factor + Math.sin(i * 1.5) * 0.3).toFixed(2),
                        [secB ? secB.sector : 'Sector B']: +(changeB * factor + Math.cos(i * 1.5) * 0.3).toFixed(2)
                      };
                    });
                  })()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="time" stroke="#a1a1aa" fontSize={10} tickLine={false} />
                    <YAxis stroke="#a1a1aa" fontSize={10} tickFormatter={(val) => `${val}%`} />
                    <Tooltip contentStyle={{ backgroundColor: '#121214', borderColor: '#27272a', borderRadius: '8px', color: '#fafafa', fontSize: '11px' }} formatter={(val: any) => [`${val}%`, 'Change']} />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Line type="monotone" dataKey={comparedSectors[0] || PSX_HEATMAP_DATA[0].sector} stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey={comparedSectors[1] || PSX_HEATMAP_DATA[1].sector} stroke="#10b981" strokeWidth={2.5} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-3.5 space-y-3">
              <div className="flex items-center space-x-2 text-[#3b82f6] font-bold text-xs"><Sparkles className="w-4 h-4" /><span>AI QUANT RELATIVE COMPARISON SYNTHESIS</span></div>
              <p className="text-[11px] text-[#a1a1aa] leading-relaxed font-sans">
                Comparing <strong className="text-[#fafafa]">{comparedSectors[0] || 'Sector A'}</strong> with <strong className="text-[#fafafa]">{comparedSectors[1] || 'Sector B'}</strong> reveals distinct risk-reward profiles. {comparedSectors[0] || 'Sector A'} offers higher dividend yield support in an easing monetary environment, whereas {comparedSectors[1] || 'Sector B'} provides greater beta sensitivity for capital growth.
              </p>
              <div className="flex items-center justify-end pt-2 border-t border-[#27272a]">
                <button onClick={() => { const sA = comparedSectors[0] || PSX_HEATMAP_DATA[0].sector; const sB = comparedSectors[1] || PSX_HEATMAP_DATA[1].sector; setIsCompareModalOpen(false); if (onAskAgent) onAskAgent(`QuantAgent, compare trade opportunities between the ${sA} sector and ${sB} sector. Which sector has better risk-adjusted return potential over the next 3 to 6 months based on macro interest rates and sentiment?`); }} className="px-4 py-2 bg-[#10b981] hover:bg-[#059669] text-white font-mono font-bold text-xs rounded transition-all flex items-center space-x-2 cursor-pointer shadow-md">
                  <Bot className="w-4 h-4" /><span>Ask QuantAgent to Compare Trade Options</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-[#121214] border border-[#27272a] rounded-lg overflow-hidden shadow-lg mt-6">
        <div className="bg-[#18181b] px-4 py-2 border-b border-[#27272a] flex items-center justify-between font-mono text-xs">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-ping" />
            <span className="font-bold text-[#fafafa] uppercase tracking-wider text-[11px] flex items-center gap-1.5"><RefreshCw className="w-3.5 h-3.5 text-[#10b981] animate-spin" />PSX SECTOR REAL-TIME TICKER</span>
          </div>
          <span className="text-[10px] text-[#a1a1aa]">Hover to Pause • Click Sector to Isolate</span>
        </div>
        <div className="py-3 bg-[#09090b] overflow-hidden relative">
          <div className="animate-ticker space-x-6 px-4">
            {[...PSX_HEATMAP_DATA, ...PSX_HEATMAP_DATA].map((sec, idx) => (
              <div key={`${sec.sector}-${idx}`} onClick={() => setSelectedSector(sec.sector)} className="inline-flex items-center space-x-2 px-3 py-1.5 bg-[#121214] hover:bg-[#27272a] border border-[#27272a] hover:border-[#3b82f6] rounded cursor-pointer transition-all shrink-0 font-mono text-xs">
                <span className="font-bold text-[#fafafa]">{sec.sector}</span>
                <span className={`font-extrabold px-1.5 py-0.2 rounded text-[11px] ${sec.avgChangePct >= 0 ? 'bg-[#10b981]/15 text-[#10b981]' : 'bg-[#ef4444]/15 text-[#ef4444]'}`}>
                  {sec.avgChangePct > 0 ? `+${sec.avgChangePct}%` : `${sec.avgChangePct}%`}
                </span>
                <span className="text-[10px] text-[#a1a1aa] border-l border-[#27272a] pl-2">MCap: {sec.totalMarketCapBillion}B</span>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
};
