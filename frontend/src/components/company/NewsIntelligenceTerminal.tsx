"use client";

/**
 * PSX News Intelligence Terminal
 * Adapted from the PSX WorldMonitor terminal design.
 * Provides: macro ticker banner, category/sentiment/ticker filters,
 * enhanced news cards with transmission paths and trend projections,
 * a news detail modal, and a quant alerts rules engine.
 *
 * All data here is static sample intelligence — not a live feed.
 * Live feed integration depends on future backend work.
 */

import { useState } from "react";
import {
  TrendingUp, TrendingDown, Minus, Flame, ChevronRight, Sparkles,
  BarChart3, ExternalLink, Bell, Plus, Trash2, ArrowRight,
  CheckCircle2, ShieldAlert, Zap, X,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type NewsCategory = "ALL" | "PSX_EQUITIES" | "GEOPOLITICS" | "MACRO_SBP_IMF" | "COMMODITIES_FX" | "QUANT_SIGNALS";
type SentimentType = "BULLISH" | "BEARISH" | "NEUTRAL";
type ImpactHorizon = "INTRADAY" | "1-WEEK" | "1-MONTH" | "3-MONTHS";

interface TrendProjection {
  bullCase: string;
  baseCase: string;
  bearCase: string;
  probabilityBull: number;
  probabilityBear: number;
  expectedIndexDelta: string;
  affectedSectors: string[];
}

interface IntelItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: string;
  category: NewsCategory;
  tickers: string[];
  sentiment: SentimentType;
  sentimentScore: number;
  volatilityScore: number;
  impactHorizon: ImpactHorizon;
  aiAnalysis: string;
  trendProjection: TrendProjection;
  geopoliticalRegion?: string;
  isBreaking?: boolean;
  url?: string;
  transmissionPath?: string[];
}

interface AlertRule {
  id: string;
  name: string;
  category: NewsCategory;
  tickerFilter?: string;
  minSentimentScore?: number;
  minVolatility?: number;
  keyword?: string;
  active: boolean;
  createdTime: string;
}

interface AlertNotification {
  id: string;
  ruleName: string;
  item: IntelItem;
  timestamp: string;
}

// ─── Static intelligence seed data (fertilizer sector focus) ─────────────────

const STATIC_INTEL: IntelItem[] = [
  {
    id: "intel-1",
    title: "IMF Approves $1.1B Tranche; Circular Debt Clearance Timeline Demanded — Direct FFC/EFERT Catalyst",
    summary: "IMF staff-level agreement paves the way for immediate disbursement. Fund emphasised fast-tracking the Circular Debt Management Plan, which directly affects gas receivables owed to fertilizer producers.",
    source: "Reuters / IMF Press Release",
    publishedAt: "2 hrs ago",
    category: "MACRO_SBP_IMF",
    tickers: ["FFC", "EFERT", "FATIMA", "HUBC", "OGDC"],
    sentiment: "BULLISH",
    sentimentScore: 81,
    volatilityScore: 8,
    impactHorizon: "1-MONTH",
    geopoliticalRegion: "Washington / IMF",
    isBreaking: true,
    aiAnalysis: "IMF conditionality forcing circular debt resolution (currently >PKR 2.4T) is the single biggest catalyst for fertilizer-sector balance sheets. Gas receivable settlement will directly boost FFC and EFERT cash positions, removing dividend overhang and reducing short-term financing needs.",
    transmissionPath: [
      "IMF SLA achieved for $1.1B tranche",
      "Bilateral credit lines from Gulf allies unlocked",
      "Government executes gas circular debt payout to fertilizer companies",
      "FFC & EFERT cash balances surge; dividend capacity strengthened",
    ],
    trendProjection: {
      bullCase: "Circular debt cash payout executed fully: FFC and EFERT trigger circuit uppers (+7.5%) on announcement day.",
      baseCase: "Tranche released on schedule; fertilizer names rally 3-5% over 2 weeks as sentiment improves.",
      bearCase: "Utility tariff protests slow implementation; delay in energy sector settlement — stocks trade sideways.",
      probabilityBull: 68,
      probabilityBear: 15,
      expectedIndexDelta: "+800 to +1,400 pts",
      affectedSectors: ["Fertilizer", "Power Generation & Distribution", "Oil & Gas Exploration"],
    },
  },
  {
    id: "intel-2",
    title: "Fertilizer Sector Gas Tariff Re-indexation Proposal: FFC & EFERT Yield Calculations Updated",
    summary: "Ministry of Energy submitted a proposal to align feed gas prices across old and new fertilizer plants. Quant yield models evaluate net impact on payout ratios for FFC, ENGRO, EFERT, and FATIMA.",
    source: "Business Recorder / Ministry of Energy",
    publishedAt: "3 hrs ago",
    category: "COMMODITIES_FX",
    tickers: ["FFC", "EFERT", "FATIMA"],
    sentiment: "NEUTRAL",
    sentimentScore: 5,
    volatilityScore: 5,
    impactHorizon: "1-MONTH",
    geopoliticalRegion: "Pakistan Macro",
    isBreaking: false,
    aiAnalysis: "Gas tariff unification increases input costs for certain legacy plants by ~8-12%. However, strong pricing power allows fertilizer producers to pass costs to urea retail prices. Dividend yields above 16% provide downside protection for institutional holders.",
    transmissionPath: [
      "Ministry proposes unified feed gas tariff for fertilizer units",
      "Input cost increases by ~8-12% for select legacy plants",
      "Urea price pass-through expected within 14 days via NFDC circular",
      "EBITDA impact remains broadly neutral due to inelastic agricultural demand",
    ],
    trendProjection: {
      bullCase: "Urea price adjustment fully offsets gas hike: Dividend yields sustained at 17%; accumulation continues.",
      baseCase: "Minor temporary margin squeeze; stocks trade sideways with high dividend accumulation.",
      bearCase: "Government imposes urea price cap: FFC & EFERT margins decline 3-5%; dividend cut risk rises.",
      probabilityBull: 45,
      probabilityBear: 25,
      expectedIndexDelta: "-50 to +80 pts",
      affectedSectors: ["Fertilizer"],
    },
  },
  {
    id: "intel-3",
    title: "SBP Policy Rate Cut to 11% — Real Rates Positive at +480 bps; Leveraged Fertilizer Names Re-rate",
    summary: "State Bank monetary committee confirms inflation stable at 6.2% YoY, with real interest rates among highest in EM universe. Fertilizer sector benefits via lower short-term borrowing costs for working capital.",
    source: "State Bank of Pakistan / Business Recorder",
    publishedAt: "34 mins ago",
    category: "MACRO_SBP_IMF",
    tickers: ["FFC", "EFERT", "FATIMA", "MCB", "LUCK"],
    sentiment: "BULLISH",
    sentimentScore: 85,
    volatilityScore: 7,
    impactHorizon: "1-MONTH",
    geopoliticalRegion: "Pakistan Macro",
    isBreaking: false,
    aiAnalysis: "Rate cut cycles in Pakistan historically trigger re-rating in high-dividend names. Fertilizer companies with large short-term working capital lines benefit directly from lower finance costs. EFERT's interest coverage ratio improvement is most material — estimated 15-18% uplift in finance cost savings.",
    transmissionPath: [
      "CPI falls to 6.2% YoY → real interest rate hits +4.8%",
      "SBP signals policy rate reduction toward single digits",
      "Fertilizer company working capital finance costs drop 150-200 bps",
      "Valuation multiples expand for high-dividend names across KSE-100",
    ],
    trendProjection: {
      bullCase: "SBP cuts 150 bps in next MPS: Fertilizer stocks surge +8% to +12% on re-rating.",
      baseCase: "100 bps cut priced in: Gradual accumulation in FFC, FATIMA with improving dividend coverage.",
      bearCase: "Inflation rebounds on utility tariff hike: Cut postponed, temporary pause in sector momentum.",
      probabilityBull: 70,
      probabilityBear: 10,
      expectedIndexDelta: "+1,200 to +1,800 pts",
      affectedSectors: ["Fertilizer", "Cement", "Technology", "Commercial Banks"],
    },
  },
  {
    id: "intel-4",
    title: "Brent Crude Surges +4% on Hormuz Shipping Disruption — Indirect Negative for Pakistan Energy Chain",
    summary: "Shipping disruptions at the Strait of Hormuz push Brent above $78/bbl. Pakistan's fuel import bill increases, adding pressure to trade deficit and PKR/USD stability — indirect headwind for fertilizer input costs.",
    source: "Reuters / Platts Energy",
    publishedAt: "58 mins ago",
    category: "GEOPOLITICS",
    tickers: ["OGDC", "PPL", "FFC", "EFERT"],
    sentiment: "BEARISH",
    sentimentScore: -62,
    volatilityScore: 9,
    impactHorizon: "1-WEEK",
    geopoliticalRegion: "Middle East / Gulf",
    isBreaking: false,
    aiAnalysis: "Elevated crude prices widen Pakistan's trade deficit by an estimated $120-150M/month at $78/bbl. This increases PKR depreciation pressure, which in turn raises LNG import costs — a direct input for certain fertilizer plants. E&P names (OGDC, PPL) benefit domestically from higher crude benchmarks.",
    transmissionPath: [
      "Hormuz shipping disruption → Brent surges above $78/bbl",
      "Pakistan LNG import costs increase by ~$0.8/MMBTU",
      "RLNG-based fertilizer plants face higher feedstock costs",
      "PKR depreciation pressure adds 2-3% to net import bill",
    ],
    trendProjection: {
      bullCase: "Disruption resolves quickly: Crude retraces to $74/bbl; PKR stabilises within 72 hours.",
      baseCase: "Moderate impact: Fertilizer margins dip 1-2%, offset by urea price adjustments over 30 days.",
      bearCase: "Sustained crude above $85/bbl: LNG cost shock materially compresses fertilizer sector margins.",
      probabilityBull: 35,
      probabilityBear: 30,
      expectedIndexDelta: "-200 to +100 pts",
      affectedSectors: ["Fertilizer", "Refineries", "Power Generation"],
    },
  },
  {
    id: "intel-5",
    title: "Global EM Fund Flows Positive: Frontier Pakistan Allocation Increases on High Real Yield Story",
    summary: "Emerging market equity funds report net inflows of $3.4B this week. Pakistan's frontier-market allocation score increases as PKR stability and 16%+ dividend yields on blue chips attract institutional interest.",
    source: "Financial Times / MSCI Frontier Index",
    publishedAt: "4 hrs ago",
    category: "QUANT_SIGNALS",
    tickers: ["FFC", "MCB", "OGDC", "SYS"],
    sentiment: "BULLISH",
    sentimentScore: 74,
    volatilityScore: 5,
    impactHorizon: "3-MONTHS",
    geopoliticalRegion: "Global EM",
    isBreaking: false,
    aiAnalysis: "Lower US Dollar yields reduce cost of capital globally and encourage portfolio managers to seek yield in high-real-return frontier markets. PSX trades at a forward P/E of ~4.8x vs. MSCI Frontier average of 8.2x. FFC's 16%+ dividend yield is among the highest in the EM universe for commodity producers.",
    transmissionPath: [
      "US Fed maintains dovish tone → global EM risk appetite improves",
      "Frontier market fund managers increase Pakistan allocation weight",
      "FIPI net inflow into PSX blue chips including fertilizer and E&P",
      "KSE-100 liquidity improves; foreign participation rises",
    ],
    trendProjection: {
      bullCase: "Pakistan re-enters MSCI Emerging Markets watchlist: Institutional re-rating of 15-20% over 6 months.",
      baseCase: "Steady foreign accumulation in high-dividend names; KSE-100 grinds to 120K over 3 months.",
      bearCase: "Global risk-off on US recession fears: EM outflows resume, reducing PSX foreign participation.",
      probabilityBull: 55,
      probabilityBear: 20,
      expectedIndexDelta: "+600 to +1,200 pts",
      affectedSectors: ["Fertilizer", "Commercial Banks", "Oil & Gas Exploration"],
    },
  },
];

// ─── Macro indicator seed data ─────────────────────────────────────────────────

const MACRO_INDICATORS = [
  { id: "kse100", label: "KSE-100", value: "114,850", change: "+620", status: "up" as const },
  { id: "sbp", label: "SBP Rate", value: "11.00%", change: "-100 bps", status: "down" as const },
  { id: "usdpkr", label: "USD/PKR", value: "278.45", change: "-0.35", status: "down" as const },
  { id: "brent", label: "Brent Crude", value: "$76.80", change: "+$1.45", status: "up" as const },
  { id: "reserves", label: "SBP Reserves", value: "$14.28B", change: "+$180M", status: "up" as const },
  { id: "cpi", label: "CPI YoY", value: "6.20%", change: "-0.70%", status: "down" as const },
  { id: "pkrv10", label: "10Y PKRV", value: "11.85%", change: "-12 bps", status: "down" as const },
];

const CATEGORY_LIST: { key: NewsCategory; label: string }[] = [
  { key: "ALL", label: "All Intelligence" },
  { key: "PSX_EQUITIES", label: "PSX Companies" },
  { key: "GEOPOLITICS", label: "Geopolitics" },
  { key: "MACRO_SBP_IMF", label: "Macro / SBP / IMF" },
  { key: "COMMODITIES_FX", label: "Commodities & FX" },
  { key: "QUANT_SIGNALS", label: "Quant Signals" },
];

const POPULAR_TICKERS = ["FFC", "EFERT", "FATIMA", "AGL", "OGDC", "PPL", "MCB", "LUCK", "SYS", "HUBC"];

const INITIAL_ALERT_RULES: AlertRule[] = [
  {
    id: "rule-1",
    name: "High-Volatility Fertilizer Alert",
    category: "COMMODITIES_FX",
    tickerFilter: "FFC,EFERT,FATIMA",
    minVolatility: 7,
    active: true,
    createdTime: "System Default",
  },
  {
    id: "rule-2",
    name: "IMF / SBP Breaking News",
    category: "MACRO_SBP_IMF",
    minSentimentScore: 60,
    keyword: "IMF,SBP,Rate",
    active: true,
    createdTime: "System Default",
  },
];

// ─── Sub-components ────────────────────────────────────────────────────────────

function MacroTicker() {
  return (
    <div className="overflow-hidden border-y border-[#27272a] bg-[#09090b] py-2">
      <div className="flex animate-[ticker_30s_linear_infinite] gap-8 whitespace-nowrap">
        {[...MACRO_INDICATORS, ...MACRO_INDICATORS].map((ind, i) => (
          <span key={i} className="inline-flex items-center gap-2 text-xs font-mono">
            <span className="text-[#a1a1aa]">{ind.label}</span>
            <span className="font-bold text-[#fafafa]">{ind.value}</span>
            <span className={ind.status === "up" ? "text-[#10b981]" : "text-[#ef4444]"}>
              {ind.change}
            </span>
            <span className="text-[#3f3f46]">·</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function SentimentPill({ item }: { item: IntelItem }) {
  const isBull = item.sentiment === "BULLISH";
  const isBear = item.sentiment === "BEARISH";
  return (
    <div className={`flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-mono font-bold uppercase tracking-wide
      ${isBull ? "border-[#10b981]/30 bg-[#10b981]/10 text-[#10b981]"
        : isBear ? "border-[#ef4444]/30 bg-[#ef4444]/10 text-[#ef4444]"
        : "border-[#3f3f46] bg-[#27272a] text-[#a1a1aa]"}`}>
      {isBull && <TrendingUp className="h-3 w-3" />}
      {isBear && <TrendingDown className="h-3 w-3" />}
      {!isBull && !isBear && <Minus className="h-3 w-3" />}
      <span>{item.sentimentScore > 0 ? `+${item.sentimentScore}` : item.sentimentScore} {item.sentiment}</span>
    </div>
  );
}

function NewsCard({
  item,
  onOpenDetail,
  onSelectTicker,
}: {
  item: IntelItem;
  onOpenDetail: (item: IntelItem) => void;
  onSelectTicker: (t: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="group rounded-lg border border-[#27272a] bg-[#121214] p-5 shadow-sm transition-all hover:border-[#3f3f46] hover:bg-[#18181b] space-y-4">
      {/* Header row */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#27272a] pb-3">
        <div className="flex items-center gap-2">
          <span className="rounded border border-[#27272a] bg-[#18181b] px-2.5 py-0.5 text-[11px] font-mono font-bold text-[#fafafa]">
            {item.category.replace(/_/g, " ")}
          </span>
          {item.geopoliticalRegion && (
            <span className="rounded border border-[#27272a] bg-[#09090b] px-2 py-0.5 text-[10px] font-mono text-[#a1a1aa]">
              📍 {item.geopoliticalRegion}
            </span>
          )}
          <span className="text-xs font-mono text-[#a1a1aa]">· {item.source}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-[#a1a1aa]">{item.publishedAt}</span>
          <span className="rounded border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-mono font-semibold text-amber-400">
            VOL {item.volatilityScore}/10
          </span>
          <SentimentPill item={item} />
        </div>
      </div>

      {/* Title + summary */}
      <div className="space-y-2">
        <h3
          onClick={() => onOpenDetail(item)}
          className="cursor-pointer text-base font-semibold text-[#fafafa] leading-snug transition-colors group-hover:text-[#3b82f6]"
        >
          {item.title}
        </h3>
        <p className="text-xs text-[#a1a1aa] leading-relaxed">{item.summary}</p>

        {/* Tickers + horizon */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="mr-1 text-[11px] font-mono text-[#a1a1aa]">AFFECTED ASSETS:</span>
          {item.tickers.map((t) => (
            <button
              key={t}
              onClick={() => onSelectTicker(t)}
              className="rounded border border-[#27272a] bg-[#18181b] px-2 py-0.5 text-xs font-mono font-bold text-[#3b82f6] transition-all hover:border-[#3b82f6]/50 hover:bg-[#3b82f6]/20"
            >
              ${t}
            </button>
          ))}
          <span className="ml-auto rounded border border-[#27272a] bg-[#09090b] px-2 py-0.5 text-[10px] font-mono text-[#a1a1aa]">
            HORIZON: {item.impactHorizon}
          </span>
        </div>
      </div>

      {/* Transmission path */}
      {item.transmissionPath && item.transmissionPath.length > 0 && (
        <div className="rounded-lg border border-[#27272a] bg-[#18181b] p-3 space-y-1.5">
          <span className="block text-[10px] font-mono font-semibold uppercase tracking-wider text-[#3b82f6]">
            ⚡ FINANCIAL TRANSMISSION PATH:
          </span>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-4 text-xs font-mono">
            {item.transmissionPath.map((step, idx) => (
              <div key={idx} className="flex items-center gap-1.5 rounded border border-[#27272a] bg-[#09090b] p-1.5">
                <span className="shrink-0 text-[10px] font-bold text-[#3b82f6]">0{idx + 1}.</span>
                <span className="truncate text-[11px] text-[#a1a1aa]">{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trend projection (expandable) */}
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-between rounded-lg border border-[#27272a] bg-[#18181b] px-3 py-2 text-xs font-mono font-semibold text-[#a1a1aa] transition-all hover:bg-[#27272a] hover:text-[#fafafa]"
        >
          <div className="flex items-center gap-2 text-[#3b82f6]">
            <Sparkles className="h-3.5 w-3.5" />
            <span>QUANT SCENARIO & TREND PROJECTION MODEL</span>
          </div>
          <div className="flex items-center gap-2 text-[#a1a1aa]">
            <span>Expected Index Delta: <strong className="text-[#fafafa]">{item.trendProjection.expectedIndexDelta}</strong></span>
            <ChevronRight className={`h-4 w-4 transition-transform ${expanded ? "rotate-90" : ""}`} />
          </div>
        </button>

        {expanded && (
          <div className="mt-2 rounded-lg border border-[#27272a] bg-[#09090b] p-4 space-y-3 font-mono text-xs">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-[#10b981]/30 bg-[#10b981]/10 p-3 space-y-1">
                <span className="block font-bold text-[#10b981]">BULL CASE ({item.trendProjection.probabilityBull}%)</span>
                <p className="text-[11px] text-[#fafafa] leading-normal">{item.trendProjection.bullCase}</p>
              </div>
              <div className="rounded-lg border border-[#27272a] bg-[#18181b] p-3 space-y-1">
                <span className="block font-bold text-[#fafafa]">BASE CASE</span>
                <p className="text-[11px] text-[#a1a1aa] leading-normal">{item.trendProjection.baseCase}</p>
              </div>
              <div className="rounded-lg border border-[#ef4444]/30 bg-[#ef4444]/10 p-3 space-y-1">
                <span className="block font-bold text-[#ef4444]">BEAR CASE ({item.trendProjection.probabilityBear}%)</span>
                <p className="text-[11px] text-[#fafafa] leading-normal">{item.trendProjection.bearCase}</p>
              </div>
            </div>
            {item.trendProjection.affectedSectors.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-[#a1a1aa]">
                <span>Sector Impact Coverage:</span>
                {item.trendProjection.affectedSectors.map((s) => (
                  <span key={s} className="rounded border border-[#27272a] bg-[#18181b] px-2 py-0.5 text-[#fafafa]">{s}</span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer actions */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#27272a] pt-2">
        <button
          onClick={() => onOpenDetail(item)}
          className="flex items-center gap-1.5 rounded-md border border-[#3b82f6]/30 bg-[#3b82f6]/10 px-3 py-1.5 text-xs font-mono font-semibold text-[#3b82f6] transition-all hover:bg-[#3b82f6]/20"
        >
          <BarChart3 className="h-3.5 w-3.5" />
          <span>Deep Analysis</span>
        </button>
        {item.url && (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-md border border-[#27272a] bg-[#18181b] px-3 py-1.5 text-xs font-mono text-[#a1a1aa] transition-all hover:text-[#fafafa]"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span>Source</span>
          </a>
        )}
        <span className="ml-auto text-[11px] font-mono text-[#a1a1aa]">AI Grounded Evaluation</span>
      </div>
    </div>
  );
}

function NewsDetailModal({ item, onClose }: { item: IntelItem | null; onClose: () => void }) {
  if (!item) return null;
  const isBull = item.sentiment === "BULLISH";
  const isBear = item.sentiment === "BEARISH";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-[#334155] bg-[#0e131f] p-6 shadow-2xl space-y-6 font-mono">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[#334155] pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="rounded border border-[#334155] bg-[#1e293b] px-2.5 py-0.5 text-[11px] font-bold text-slate-300">
                {item.category.replace(/_/g, " ")}
              </span>
              {item.geopoliticalRegion && (
                <span className="rounded bg-slate-900 px-2 py-0.5 text-[10px] text-slate-400">
                  📍 {item.geopoliticalRegion}
                </span>
              )}
              <span className="text-xs text-slate-400">· {item.source}</span>
            </div>
            <h2 className="mt-2 text-lg font-bold leading-snug text-slate-100">{item.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 rounded-lg border border-slate-800 bg-slate-900 p-2 text-slate-400 transition-all hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Score grid */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            {
              label: "AI SENTIMENT SCORE",
              value: (
                <span className={`flex items-center text-sm font-bold ${isBull ? "text-emerald-400" : isBear ? "text-rose-400" : "text-slate-300"}`}>
                  {isBull && <TrendingUp className="mr-1 h-4 w-4" />}
                  {isBear && <TrendingDown className="mr-1 h-4 w-4" />}
                  {!isBull && !isBear && <Minus className="mr-1 h-4 w-4" />}
                  {item.sentimentScore > 0 ? `+${item.sentimentScore}` : item.sentimentScore} {item.sentiment}
                </span>
              ),
            },
            { label: "VOLATILITY RATING", value: <span className="text-sm font-bold text-amber-400">{item.volatilityScore}/10</span> },
            { label: "IMPACT HORIZON", value: <span className="text-sm font-bold text-slate-200">{item.impactHorizon}</span> },
            { label: "EXPECTED DELTA", value: <span className="text-sm font-bold text-emerald-400">{item.trendProjection.expectedIndexDelta}</span> },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-xl border border-slate-800 bg-[#121826] p-3 space-y-1">
              <span className="block text-[10px] uppercase text-slate-400">{label}</span>
              {value}
            </div>
          ))}
        </div>

        {/* Affected tickers */}
        <div className="space-y-2">
          <span className="block text-xs font-bold uppercase text-slate-300">AFFECTED PSX EQUITIES:</span>
          <div className="flex flex-wrap gap-2">
            {item.tickers.map((t) => (
              <span key={t} className="rounded-lg border border-emerald-500/40 bg-emerald-950/60 px-3 py-1 text-xs font-bold text-emerald-400">
                ${t}
              </span>
            ))}
          </div>
        </div>

        {/* Summary */}
        <div className="space-y-2">
          <span className="block text-xs font-bold uppercase text-slate-300">EXECUTIVE SUMMARY:</span>
          <p className="rounded-xl border border-slate-800 bg-[#121826] p-4 text-xs leading-relaxed text-slate-200">{item.summary}</p>
        </div>

        {/* AI analysis */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase text-emerald-400">
            <BarChart3 className="h-4 w-4" />
            <span>IN-DEPTH FINANCIAL TRANSMISSION & EARNINGS IMPACT:</span>
          </div>
          <p className="rounded-xl border border-slate-800 bg-[#121826] p-4 text-xs leading-relaxed text-slate-300">{item.aiAnalysis}</p>
        </div>

        {/* Transmission chain */}
        {item.transmissionPath && (
          <div className="space-y-2">
            <span className="block text-xs font-bold uppercase text-slate-300">STEP-BY-STEP TRANSMISSION CHAIN:</span>
            <div className="space-y-1.5">
              {item.transmissionPath.map((step, idx) => (
                <div key={idx} className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#121826] p-2.5 text-xs">
                  <span className="font-bold text-emerald-400">0{idx + 1}.</span>
                  <span className="text-slate-200">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Scenarios */}
        <div className="space-y-2">
          <span className="block text-xs font-bold uppercase text-slate-300">QUANT SCENARIO TREE:</span>
          <div className="grid grid-cols-1 gap-3 text-xs md:grid-cols-3">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-3 space-y-1">
              <span className="block font-bold text-emerald-400">BULL CASE ({item.trendProjection.probabilityBull}%)</span>
              <p className="text-[11px] leading-relaxed text-slate-300">{item.trendProjection.bullCase}</p>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900 p-3 space-y-1">
              <span className="block font-bold text-slate-200">BASE CASE</span>
              <p className="text-[11px] leading-relaxed text-slate-300">{item.trendProjection.baseCase}</p>
            </div>
            <div className="rounded-xl border border-rose-500/30 bg-rose-950/30 p-3 space-y-1">
              <span className="block font-bold text-rose-400">BEAR CASE ({item.trendProjection.probabilityBear}%)</span>
              <p className="text-[11px] leading-relaxed text-slate-300">{item.trendProjection.bearCase}</p>
            </div>
          </div>
        </div>

        <div className="flex justify-end border-t border-slate-800 pt-4">
          <button onClick={onClose} className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-700">
            Close Window
          </button>
        </div>
      </div>
    </div>
  );
}

function AlertsPanel() {
  const [rules, setRules] = useState<AlertRule[]>(INITIAL_ALERT_RULES);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [category, setCategory] = useState<NewsCategory>("ALL");
  const [ticker, setTicker] = useState("");
  const [minSentiment, setMinSentiment] = useState(60);
  const [minVol, setMinVol] = useState(6);
  const [keyword, setKeyword] = useState("");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setRules((prev) => [
      ...prev,
      { id: `rule-${Date.now()}`, name, category, tickerFilter: ticker, minSentimentScore: minSentiment, minVolatility: minVol, keyword, active: true, createdTime: new Date().toLocaleDateString() },
    ]);
    setName(""); setTicker(""); setKeyword(""); setShowCreate(false);
  };

  return (
    <div className="space-y-4 font-mono">
      <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-[#0e131f] p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
            <Bell className="h-4 w-4" />
            QUANT ALERT & NOTIFICATION ENGINE
          </div>
          <h4 className="text-lg font-bold text-slate-100">Customizable Alert Rules</h4>
          <p className="mt-0.5 text-xs text-slate-400">Configure threshold rules on sentiment scores, volatility, tickers, or keywords.</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex shrink-0 items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-lg transition-all hover:bg-emerald-500"
        >
          <Plus className="h-4 w-4" /> Create Alert Rule
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Rules list */}
        <div className="rounded-xl border border-slate-800 bg-[#0e131f] p-5 space-y-4 shadow-xl lg:col-span-7">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h5 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-200">
              <Zap className="h-4 w-4 text-emerald-400" />
              ACTIVE ALERT RULES ({rules.length})
            </h5>
            <span className="text-xs text-slate-400">Monitoring Intel Stream</span>
          </div>
          <div className="space-y-3">
            {rules.map((rule) => (
              <div key={rule.id} className={`rounded-xl border p-4 transition-all ${rule.active ? "border-slate-800 bg-[#121826] hover:border-slate-700" : "border-slate-900 bg-[#090c12] opacity-60"}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-100">{rule.name}</span>
                      <span className={`rounded border px-2 py-0.5 text-[10px] font-bold ${rule.active ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : "border-0 bg-slate-800 text-slate-500"}`}>
                        {rule.active ? "ACTIVE" : "PAUSED"}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400">
                      <span>Category: <strong className="text-slate-200">{rule.category}</strong></span>
                      {rule.tickerFilter && <span>· Tickers: <strong className="text-emerald-400">{rule.tickerFilter}</strong></span>}
                      {rule.minSentimentScore && <span>· Sentiment ≥ |{rule.minSentimentScore}|</span>}
                      {rule.minVolatility && <span>· Vol ≥ {rule.minVolatility}/10</span>}
                      {rule.keyword && <span>· Keywords: <strong className="text-slate-200">{rule.keyword}</strong></span>}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <button
                      onClick={() => setRules((prev) => prev.map((r) => r.id === rule.id ? { ...r, active: !r.active } : r))}
                      className={`rounded border px-3 py-1 text-xs font-bold transition-all ${rule.active ? "border-amber-500/40 bg-amber-500/20 text-amber-400 hover:bg-amber-500/30" : "border-emerald-500/40 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"}`}
                    >
                      {rule.active ? "Pause" : "Activate"}
                    </button>
                    <button
                      onClick={() => setRules((prev) => prev.filter((r) => r.id !== rule.id))}
                      className="rounded p-1.5 text-slate-500 transition-all hover:bg-rose-950/40 hover:text-rose-400"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Notifications log */}
        <div className="flex flex-col justify-between rounded-xl border border-slate-800 bg-[#0e131f] p-5 shadow-xl lg:col-span-5">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h5 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-200">
                <ShieldAlert className="h-4 w-4 text-rose-400" />
                NOTIFICATIONS ({notifications.length})
              </h5>
              {notifications.length > 0 && (
                <button onClick={() => setNotifications([])} className="text-xs text-slate-400 underline hover:text-slate-200">Clear All</button>
              )}
            </div>
            <div className="mt-3 max-h-60 space-y-3 overflow-y-auto pr-1">
              {notifications.length > 0 ? notifications.map((n) => (
                <div key={n.id} className="rounded-lg border border-slate-800 bg-[#121826] p-3 space-y-1.5">
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="rounded border border-rose-500/30 bg-rose-950/60 px-2 py-0.5 font-bold text-rose-400">⚡ {n.ruleName}</span>
                    <span className="text-slate-500">{n.timestamp}</span>
                  </div>
                  <h6 className="line-clamp-2 text-xs font-bold text-slate-100">{n.item.title}</h6>
                  <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                    <span>Sentiment: <strong className="text-emerald-400">{n.item.sentimentScore} {n.item.sentiment}</strong></span>
                    <span className="flex items-center font-bold text-emerald-400">Inspect <ArrowRight className="ml-0.5 h-3 w-3" /></span>
                  </div>
                </div>
              )) : (
                <div className="space-y-2 p-8 text-center text-xs text-slate-500">
                  <CheckCircle2 className="mx-auto h-8 w-8 text-slate-600" />
                  <p>No alert triggers logged this session.</p>
                </div>
              )}
            </div>
          </div>
          <p className="border-t border-slate-800 pt-3 text-[11px] text-slate-400">Rules evaluate against incoming intelligence stream items.</p>
        </div>
      </div>

      {/* Create rule modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-[#0e131f] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-slate-100">Create Quant Alert Rule</h3>
              <button onClick={() => setShowCreate(false)} className="font-bold text-slate-400 hover:text-white">✕</button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4 text-xs font-mono">
              <div>
                <label className="mb-1 block font-semibold text-slate-300">Rule Name *</label>
                <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. FFC Gas Tariff Shock" className="w-full rounded-lg border border-slate-700 bg-[#141a26] p-2.5 text-slate-100 focus:border-emerald-500 focus:outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block font-semibold text-slate-300">Category</label>
                  <select value={category} onChange={(e) => setCategory(e.target.value as NewsCategory)} className="w-full rounded-lg border border-slate-700 bg-[#141a26] p-2.5 text-slate-100 focus:border-emerald-500 focus:outline-none">
                    {CATEGORY_LIST.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block font-semibold text-slate-300">Tickers (comma-separated)</label>
                  <input value={ticker} onChange={(e) => setTicker(e.target.value)} placeholder="FFC, EFERT, FATIMA" className="w-full rounded-lg border border-slate-700 bg-[#141a26] p-2.5 text-slate-100 focus:border-emerald-500 focus:outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block font-semibold text-slate-300">Min |Sentiment| ≥ {minSentiment}</label>
                  <input type="number" min={1} max={100} value={minSentiment} onChange={(e) => setMinSentiment(Number(e.target.value))} className="w-full rounded-lg border border-slate-700 bg-[#141a26] p-2.5 text-slate-100 focus:border-emerald-500 focus:outline-none" />
                </div>
                <div>
                  <label className="mb-1 block font-semibold text-slate-300">Min Volatility ≥ {minVol}/10</label>
                  <input type="number" min={1} max={10} value={minVol} onChange={(e) => setMinVol(Number(e.target.value))} className="w-full rounded-lg border border-slate-700 bg-[#141a26] p-2.5 text-slate-100 focus:border-emerald-500 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="mb-1 block font-semibold text-slate-300">Keywords (comma-separated)</label>
                <input value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Gas, Tariff, IMF, Rate Cut" className="w-full rounded-lg border border-slate-700 bg-[#141a26] p-2.5 text-slate-100 focus:border-emerald-500 focus:outline-none" />
              </div>
              <div className="flex items-center justify-end gap-3 border-t border-slate-800 pt-4">
                <button type="button" onClick={() => setShowCreate(false)} className="rounded-lg bg-slate-800 px-4 py-2 font-bold text-slate-300 hover:bg-slate-700">Cancel</button>
                <button type="submit" className="rounded-lg bg-emerald-600 px-5 py-2 font-bold text-white shadow-lg hover:bg-emerald-500">Save Rule</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main export ──────────────────────────────────────────────────────────────

export default function NewsIntelligenceTerminal() {
  const [items] = useState<IntelItem[]>(STATIC_INTEL);
  const [category, setCategory] = useState<NewsCategory>("ALL");
  const [sentiment, setSentiment] = useState<SentimentType | "ALL">("ALL");
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState<IntelItem | null>(null);

  const filtered = items.filter((item) => {
    if (category !== "ALL" && item.category !== category) return false;
    if (sentiment !== "ALL" && item.sentiment !== sentiment) return false;
    if (selectedTicker && !item.tickers.includes(selectedTicker)) return false;
    if (search) {
      const q = search.toLowerCase();
      if (
        !item.title.toLowerCase().includes(q) &&
        !item.summary.toLowerCase().includes(q) &&
        !item.tickers.some((t) => t.toLowerCase().includes(q))
      ) return false;
    }
    return true;
  });

  const breaking = items.filter((i) => i.isBreaking);

  return (
    <div className="mt-8 space-y-6">
      {/* Section header */}
      <div className="border-t border-[#27272a] pt-6">
        <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-[#3b82f6]">
          <Zap className="h-4 w-4" />
          <span>PSX MARKET INTELLIGENCE TERMINAL</span>
        </div>
        <p className="mt-1 text-xs text-[#a1a1aa]">
          Real-time macro & geopolitical signals with quant scenario modelling. Static seed data — live feed via future backend integration.
        </p>
      </div>

      {/* Macro ticker banner */}
      <div className="overflow-hidden rounded-lg border border-[#27272a] bg-[#09090b]">
        <div className="border-b border-[#27272a] px-3 py-1.5 text-[10px] font-mono uppercase tracking-widest text-[#a1a1aa]">
          ● LIVE MACRO INDICATORS
        </div>
        <MacroTicker />
      </div>

      {/* Breaking news banner */}
      {breaking.length > 0 && (
        <div className="flex items-center justify-between gap-4 rounded-xl border border-rose-500/40 bg-gradient-to-r from-rose-950/80 via-[#0f172a] to-amber-950/80 p-3 shadow-lg sm:p-4">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex shrink-0 animate-pulse items-center gap-1 rounded bg-rose-600 px-2.5 py-1 text-[10px] font-mono font-bold uppercase tracking-wider text-white">
              <Flame className="h-3.5 w-3.5 fill-white" /> BREAKING
            </span>
            <p className="truncate text-sm font-semibold text-slate-100">{breaking[0].title}</p>
          </div>
          <button
            onClick={() => setDetail(breaking[0])}
            className="shrink-0 rounded border border-rose-500/40 bg-rose-500/20 px-3 py-1 text-xs font-mono font-bold text-rose-300 transition-all hover:bg-rose-500/30"
          >
            Inspect Analysis
          </button>
        </div>
      )}

      {/* Filter toolbar */}
      <div className="rounded-lg border border-[#27272a] bg-[#121214] p-4 shadow-sm space-y-4">
        {/* Category tabs */}
        <div className="flex items-center justify-between gap-2 overflow-x-auto border-b border-[#27272a] pb-3">
          <div className="flex min-w-max items-center gap-1.5">
            {CATEGORY_LIST.map((cat) => (
              <button
                key={cat.key}
                onClick={() => setCategory(cat.key)}
                className={`rounded-md px-3 py-1.5 text-xs font-mono font-medium transition-all ${
                  category === cat.key
                    ? "bg-[#3b82f6] font-bold text-white shadow-xs"
                    : "border border-[#27272a] bg-[#18181b] text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#fafafa]"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
          <span className="hidden text-xs font-mono text-[#a1a1aa] md:block">
            {filtered.length} items
          </span>
        </div>

        {/* Sentiment + tickers + search */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          {/* Sentiment pills */}
          <div className="flex items-center gap-2">
            <span className="mr-1 text-[11px] font-mono uppercase tracking-wider text-[#a1a1aa]">SENTIMENT:</span>
            {(["ALL", "BULLISH", "BEARISH", "NEUTRAL"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSentiment(s)}
                className={`flex items-center gap-1 rounded px-2.5 py-1 text-xs font-mono transition-all ${
                  sentiment === s
                    ? s === "BULLISH" ? "bg-[#10b981] font-bold text-white"
                      : s === "BEARISH" ? "bg-[#ef4444] font-bold text-white"
                      : "border border-[#3f3f46] bg-[#27272a] font-bold text-[#fafafa]"
                    : s === "BULLISH" ? "border border-[#10b981]/30 bg-[#10b981]/10 text-[#10b981] hover:bg-[#10b981]/20"
                      : s === "BEARISH" ? "border border-[#ef4444]/30 bg-[#ef4444]/10 text-[#ef4444] hover:bg-[#ef4444]/20"
                      : "bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa]"
                }`}
              >
                {s === "BULLISH" && <TrendingUp className="h-3 w-3" />}
                {s === "BEARISH" && <TrendingDown className="h-3 w-3" />}
                {s === "NEUTRAL" && <Minus className="h-3 w-3" />}
                <span>{s === "ALL" ? "All" : s.charAt(0) + s.slice(1).toLowerCase()}</span>
              </button>
            ))}
          </div>

          {/* Search */}
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search intelligence..."
            className="w-full rounded-lg border border-[#27272a] bg-[#18181b] px-3 py-1.5 text-xs font-mono text-[#fafafa] placeholder:text-[#52525b] focus:border-[#3b82f6] focus:outline-none md:w-48"
          />
        </div>

        {/* Ticker chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <span className="shrink-0 text-[11px] font-mono uppercase tracking-wider text-[#a1a1aa]">TICKERS:</span>
          {selectedTicker && (
            <button onClick={() => setSelectedTicker(null)} className="rounded bg-[#27272a] px-2 py-0.5 text-[11px] font-mono text-[#fafafa] hover:bg-[#3f3f46]">
              Clear (${selectedTicker})
            </button>
          )}
          {POPULAR_TICKERS.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedTicker(selectedTicker === t ? null : t)}
              className={`shrink-0 rounded px-2 py-0.5 text-[11px] font-mono font-bold transition-all ${
                selectedTicker === t
                  ? "bg-[#3b82f6] text-white shadow-xs"
                  : "border border-[#27272a] bg-[#18181b] text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#fafafa]"
              }`}
            >
              ${t}
            </button>
          ))}
        </div>
      </div>

      {/* News cards */}
      <div className="space-y-4">
        {filtered.map((item) => (
          <NewsCard key={item.id} item={item} onOpenDetail={setDetail} onSelectTicker={setSelectedTicker} />
        ))}
        {filtered.length === 0 && (
          <div className="rounded-lg border border-[#27272a] bg-[#121214] p-12 text-center space-y-3">
            <p className="font-mono text-sm text-[#a1a1aa]">No matching intelligence items.</p>
            <p className="text-xs text-[#52525b]">Adjust category, sentiment, or ticker filter.</p>
          </div>
        )}
      </div>

      {/* Quant alerts */}
      <AlertsPanel />

      {/* Detail modal */}
      <NewsDetailModal item={detail} onClose={() => setDetail(null)} />
    </div>
  );
}
