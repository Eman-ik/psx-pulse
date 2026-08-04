"use client";

import React from "react";
import {
  ResponsiveContainer, ComposedChart, LineChart, Bar, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
} from "recharts";
import {
  TrendingUp, TrendingDown, Minus, Shield, AlertTriangle,
  Zap, Target, Activity, CheckCircle2, XCircle, Clock, Eye,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ResearchJSON {
  ticker: string;
  fullName: string;
  exchange: string;
  analysisDate: string;
  finalPosture: "BUY" | "HOLD" | "AVOID" | "WATCHLIST" | "PRELIMINARY";
  companyHealthScore: number;
  stockAttractivenessScore: number;
  evidenceConfidence: "High" | "Medium" | "Low";
  executiveSummary: string;
  variantPerception: string;
  kpis: {
    priceLabel: string;
    marketCapLabel: string;
    peLabel: string;
    forwardPeLabel: string;
    dividendYieldLabel: string;
    roicLabel: string;
    netCashLabel: string;
    epsLabel: string;
    pbLabel: string;
    evEbitdaLabel: string;
    peValue: number | null;
    dividendYieldValue: number | null;
    roicValue: number | null;
  };
  historicalFinancials: {
    year: string;
    revenueMn: number;
    netIncomeMn: number;
    eps: number;
    fcfMn: number | null;
    grossMarginPct: number;
    netMarginPct: number;
    ocfNiRatioPct: number | null;
  }[];
  forecast: {
    year: string;
    revenueMn: number;
    netIncomeMn: number;
    eps: number;
    dps: number;
    fcfMn: number;
  }[];
  fairValueRange: { bear: number; base: number; bull: number; currentPrice: number };
  scenarios: {
    case: string;
    centralAssumption: string;
    targetPrice: number;
    totalReturnLabel: string;
    eps: number;
    probability: number;
  }[];
  thesisPillars: { pillar: string; detail: string; falsifier: string }[];
  topRisks: { risk: string; severity: string; detail: string }[];
  catalysts: { catalyst: string; timing: string; impact: string }[];
  monitoringKPIs: { kpi: string; current: string; confirms: string; breaks: string }[];
  ownership: { sponsor: number; publicFloat: number; institutional: number; foreign: number };
  sectorDrivers: { driver: string; status: string; detail: string }[];
  managementVerdict: string;
  capitalAllocationVerdict: string;
  forensicSummary: string;
  dataWarnings: string[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const POSTURE_STYLES: Record<string, { bg: string; text: string; border: string; label: string }> = {
  BUY:         { bg: "bg-positive/10",     text: "text-positive",      border: "border-positive/30",     label: "RESEARCH-QUALIFIED BUY" },
  HOLD:        { bg: "bg-accent/10",       text: "text-accent",        border: "border-accent/30",       label: "HOLD" },
  AVOID:       { bg: "bg-negative/10",     text: "text-negative",      border: "border-negative/30",     label: "AVOID" },
  WATCHLIST:   { bg: "bg-accent-yellow/10",text: "text-accent-yellow", border: "border-accent-yellow/30",label: "WATCHLIST" },
  PRELIMINARY: { bg: "bg-muted/10",        text: "text-muted",         border: "border-muted/30",        label: "PRELIMINARY" },
};

const SEVERITY_STYLES: Record<string, string> = {
  Low:      "text-positive bg-positive/10 border-positive/20",
  Medium:   "text-accent-yellow bg-accent-yellow/10 border-accent-yellow/20",
  High:     "text-orange-400 bg-orange-400/10 border-orange-400/20",
  Critical: "text-negative bg-negative/10 border-negative/20",
};

const IMPACT_STYLES: Record<string, string> = {
  Positive: "text-positive",
  Negative: "text-negative",
  Binary:   "text-accent-yellow",
};

const DRIVER_DOT: Record<string, string> = {
  positive: "bg-positive",
  neutral:  "bg-muted",
  negative: "bg-negative",
  risk:     "bg-accent-yellow",
};

const TOOLTIP_STYLE = {
  backgroundColor: "#10131c",
  borderColor: "rgba(255,255,255,0.07)",
  borderRadius: "6px",
  color: "#f5f6fa",
  fontSize: "11px",
};

function fmt(n: number | null | undefined, decimals = 0): string {
  if (n == null) return "—";
  return n.toLocaleString("en-PK", { maximumFractionDigits: decimals });
}

function fmtBn(n: number | null | undefined): string {
  if (n == null) return "—";
  return `${(n / 1000).toFixed(1)}bn`;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ScoreGauge({ score, label, color }: { score: number; label: string; color: string }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="88" height="88" viewBox="0 0 88 88">
        <circle cx="44" cy="44" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        <circle
          cx="44" cy="44" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="round"
          transform="rotate(-90 44 44)"
          style={{ transition: "stroke-dasharray 1s ease" }}
        />
        <text x="44" y="48" textAnchor="middle" fill={color} fontSize="18" fontWeight="700" fontFamily="monospace">
          {score}
        </text>
      </svg>
      <span className="text-[10px] font-mono uppercase tracking-wider text-muted text-center">{label}</span>
    </div>
  );
}

function KPICard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg px-4 py-3 space-y-0.5">
      <p className="text-[10px] font-mono uppercase tracking-wider text-muted">{label}</p>
      <p className="text-sm font-bold text-foreground font-mono">{value}</p>
      {sub && <p className="text-[10px] text-muted">{sub}</p>}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function ResearchReport({ r }: { r: ResearchJSON }) {
  const posture = POSTURE_STYLES[r.finalPosture] ?? POSTURE_STYLES.HOLD;

  // Build combined historical + forecast data for charts
  const histSorted = [...r.historicalFinancials].sort((a, b) => a.year.localeCompare(b.year));
  const allFinancials = [
    ...histSorted.map(h => ({
      year: h.year,
      revenueBn: +(h.revenueMn / 1000).toFixed(1),
      netIncomeBn: +(h.netIncomeMn / 1000).toFixed(1),
      fcfBn: h.fcfMn != null ? +(h.fcfMn / 1000).toFixed(1) : null,
      eps: h.eps,
      grossMarginPct: h.grossMarginPct,
      netMarginPct: h.netMarginPct,
      ocfNi: h.ocfNiRatioPct,
      isForecast: false,
    })),
    ...r.forecast.map(f => ({
      year: f.year,
      revenueBn: +(f.revenueMn / 1000).toFixed(1),
      netIncomeBn: +(f.netIncomeMn / 1000).toFixed(1),
      fcfBn: +(f.fcfMn / 1000).toFixed(1),
      eps: f.eps,
      dps: f.dps,
      grossMarginPct: null,
      netMarginPct: null,
      ocfNi: null,
      isForecast: true,
    })),
  ];

  const epsData = allFinancials.map(d => ({
    year: d.year,
    EPS: d.eps,
    DPS: (d as { dps?: number }).dps ?? null,
    isForecast: d.isForecast,
  }));

  const fvRange = r.fairValueRange;
  const fvSpan = fvRange.bull - fvRange.bear;

  return (
    <div className="space-y-6 font-mono text-xs">

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-mono text-muted uppercase tracking-wider">
                {r.exchange} · {r.analysisDate}
              </span>
              <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${posture.bg} ${posture.text} ${posture.border}`}>
                {posture.label}
              </span>
              <span className="text-[10px] border border-border rounded px-2 py-0.5 text-muted">
                Evidence: {r.evidenceConfidence}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-foreground">{r.ticker}</h1>
            <p className="text-sm text-muted font-sans">{r.fullName}</p>
          </div>
          <div className="flex gap-6 shrink-0">
            <ScoreGauge score={r.companyHealthScore} label="Company Health" color="#4f7cff" />
            <ScoreGauge score={r.stockAttractivenessScore} label="Stock Value" color="#22c55e" />
          </div>
        </div>

        <div className="pt-3 border-t border-border space-y-2">
          <p className="text-xs text-foreground font-sans leading-relaxed">{r.executiveSummary}</p>
          <div className="bg-surface-alt border border-border rounded-lg p-3">
            <span className="text-[10px] font-bold text-accent uppercase tracking-wider block mb-1">Variant Perception</span>
            <p className="text-xs font-sans text-muted leading-relaxed">{r.variantPerception}</p>
          </div>
        </div>
      </div>

      {/* ── KPI Row ─────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        <KPICard label="Price" value={r.kpis.priceLabel} />
        <KPICard label="Market Cap" value={r.kpis.marketCapLabel} />
        <KPICard label="Trailing P/E" value={r.kpis.peLabel} sub={`Fwd: ${r.kpis.forwardPeLabel}`} />
        <KPICard label="Dividend Yield" value={r.kpis.dividendYieldLabel} />
        <KPICard label="ROIC" value={r.kpis.roicLabel} />
        <KPICard label="EPS (TTM)" value={r.kpis.epsLabel} />
        <KPICard label="Net Cash / Debt" value={r.kpis.netCashLabel} />
        <KPICard label="P / Book" value={r.kpis.pbLabel} />
        <KPICard label="EV / EBITDA" value={r.kpis.evEbitdaLabel} />
      </div>

      {/* ── Fair Value Visual ────────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <Target className="w-3.5 h-3.5 text-accent" /> Fair Value Range
        </h3>
        <div className="relative h-12">
          <div className="absolute inset-y-3 left-0 right-0 bg-surface-alt rounded-full" />
          {/* Range bar */}
          <div
            className="absolute inset-y-3 bg-accent/20 rounded-full"
            style={{
              left: `${((fvRange.bear - fvRange.bear) / fvSpan) * 100}%`,
              right: `${((fvRange.bull - fvRange.bull) / fvSpan) * 100}%`,
              width: `${((fvRange.bull - fvRange.bear) / fvSpan) * 100}%`,
            }}
          />
          {/* Base marker */}
          <div
            className="absolute inset-y-1 w-0.5 bg-accent rounded"
            style={{ left: `${((fvRange.base - fvRange.bear) / fvSpan) * 100}%` }}
          />
          {/* Current price marker */}
          <div
            className="absolute inset-y-0 flex items-center"
            style={{ left: `${Math.min(98, Math.max(2, ((fvRange.currentPrice - fvRange.bear) / fvSpan) * 100))}%` }}
          >
            <div className="w-3 h-3 rounded-full border-2 border-accent-yellow bg-surface" />
          </div>
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono">
          <span className="text-negative">Bear PKR {fmt(fvRange.bear)}</span>
          <span className="text-accent">Base PKR {fmt(fvRange.base)}</span>
          <span className="text-positive">Bull PKR {fmt(fvRange.bull)}</span>
        </div>
        <div className="flex items-center gap-4 text-[10px] text-muted pt-1">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-accent inline-block" /> Base fair value
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full border-2 border-accent-yellow bg-surface inline-block" /> Current price PKR {fmt(fvRange.currentPrice)}
          </span>
        </div>
      </div>

      {/* ── Revenue + Net Income Chart ───────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <TrendingUp className="w-3.5 h-3.5 text-accent" /> Revenue & Net Income (PKR bn)
        </h3>
        <div className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={allFinancials} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="year" stroke="#8b92a5" tick={{ fontSize: 10, fill: "#8b92a5" }} />
              <YAxis stroke="#8b92a5" tick={{ fontSize: 10, fill: "#8b92a5" }}
                tickFormatter={v => `${v}bn`} />
              <Tooltip contentStyle={TOOLTIP_STYLE}
                formatter={(v, n) => typeof v === "number" ? [`PKR ${v}bn`, n] : [String(v), n]} />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              <Bar dataKey="revenueBn" name="Revenue" fill="#4f7cff" opacity={0.7} radius={[3, 3, 0, 0]} />
              <Bar dataKey="netIncomeBn" name="Net Income" fill="#22c55e" opacity={0.85} radius={[3, 3, 0, 0]} />
              <ReferenceLine x={histSorted[histSorted.length - 1]?.year} stroke="rgba(255,255,255,0.15)"
                strokeDasharray="4 4" label={{ value: "Forecast →", fill: "#8b92a5", fontSize: 9 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── EPS + DPS Trend ─────────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-accent" /> EPS & DPS Trend (PKR/share)
        </h3>
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={epsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="year" stroke="#8b92a5" tick={{ fontSize: 10, fill: "#8b92a5" }} />
              <YAxis stroke="#8b92a5" tick={{ fontSize: 10, fill: "#8b92a5" }}
                tickFormatter={v => `PKR ${v}`} />
              <Tooltip contentStyle={TOOLTIP_STYLE}
                formatter={(v, n) => typeof v === "number" ? [`PKR ${v}`, n] : [String(v), n]} />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              <ReferenceLine x={histSorted[histSorted.length - 1]?.year} stroke="rgba(255,255,255,0.15)"
                strokeDasharray="4 4" />
              <Line type="monotone" dataKey="EPS" stroke="#4f7cff" strokeWidth={2.5}
                dot={{ r: 4, fill: "#4f7cff" }} activeDot={{ r: 6 }} connectNulls />
              <Line type="monotone" dataKey="DPS" stroke="#22c55e" strokeWidth={2}
                dot={{ r: 3, fill: "#22c55e" }} strokeDasharray="5 3" connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Margin Trend ────────────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <BarChartIcon size={14} className="text-accent" /> Margin Profile (%)
        </h3>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={histSorted}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="year" stroke="#8b92a5" tick={{ fontSize: 10, fill: "#8b92a5" }} />
              <YAxis stroke="#8b92a5" tick={{ fontSize: 10, fill: "#8b92a5" }}
                tickFormatter={v => `${v}%`} domain={[0, "auto"]} />
              <Tooltip contentStyle={TOOLTIP_STYLE}
                formatter={(v, n) => typeof v === "number" ? [`${v.toFixed(1)}%`, n] : [String(v), n]} />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              <Line type="monotone" dataKey="grossMarginPct" name="Gross Margin"
                stroke="#4f7cff" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="netMarginPct" name="Net Margin"
                stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Scenarios ───────────────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-accent" /> Scenario Analysis
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border">
                {["Case", "Probability", "Central Assumption", "EPS (PKR)", "Target Price", "Total Return"].map(h => (
                  <th key={h} className="text-left py-2 px-3 text-muted font-semibold uppercase tracking-wider text-[10px]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {r.scenarios.map((s, i) => {
                const isPositive = s.totalReturnLabel.startsWith("+");
                const isNeg = s.totalReturnLabel.startsWith("-");
                const rowBg = s.case === "Bull" ? "hover:bg-positive/5" : s.case === "Bear" || s.case === "Stress" ? "hover:bg-negative/5" : "hover:bg-accent/5";
                return (
                  <tr key={i} className={`border-b border-border/50 ${rowBg}`}>
                    <td className="py-2.5 px-3 font-bold">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${
                        s.case === "Bull" ? "bg-positive/10 text-positive" :
                        s.case === "Base" ? "bg-accent/10 text-accent" :
                        s.case === "Bear" ? "bg-accent-yellow/10 text-accent-yellow" :
                        "bg-negative/10 text-negative"
                      }`}>{s.case}</span>
                    </td>
                    <td className="py-2.5 px-3 text-muted">{s.probability}%</td>
                    <td className="py-2.5 px-3 text-muted font-sans max-w-xs">{s.centralAssumption}</td>
                    <td className="py-2.5 px-3 font-mono">PKR {fmt(s.eps, 1)}</td>
                    <td className="py-2.5 px-3 font-mono font-bold">PKR {fmt(s.targetPrice)}</td>
                    <td className={`py-2.5 px-3 font-bold ${isPositive ? "text-positive" : isNeg ? "text-negative" : "text-muted"}`}>
                      {s.totalReturnLabel}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Thesis Pillars ──────────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-accent" /> Thesis Pillars & Falsifiers
        </h3>
        <div className="space-y-3">
          {r.thesisPillars.map((p, i) => (
            <div key={i} className="bg-surface-alt border border-border rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-accent/15 text-accent text-[10px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                <span className="font-bold text-foreground text-xs">{p.pillar}</span>
              </div>
              <p className="text-muted font-sans text-xs leading-relaxed pl-7">{p.detail}</p>
              <div className="pl-7 flex items-start gap-1.5">
                <XCircle className="w-3.5 h-3.5 text-negative shrink-0 mt-0.5" />
                <p className="text-[11px] text-negative/80 font-sans leading-snug">
                  <span className="font-bold text-negative">Falsifier:</span> {p.falsifier}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Sector Drivers + Top Risks (side by side) ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
          <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted">Sector Drivers</h3>
          <div className="space-y-2">
            {r.sectorDrivers.map((d, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${DRIVER_DOT[d.status] ?? "bg-muted"}`} />
                <div>
                  <span className="font-semibold text-foreground">{d.driver}</span>
                  <p className="text-muted font-sans text-[11px] leading-snug">{d.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
          <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-accent-yellow" /> Top Risks
          </h3>
          <div className="space-y-2">
            {r.topRisks.map((risk, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <span className={`px-1.5 py-0.5 rounded border text-[9px] font-bold shrink-0 mt-0.5 ${SEVERITY_STYLES[risk.severity] ?? "text-muted border-muted"}`}>
                  {risk.severity.toUpperCase()}
                </span>
                <div>
                  <span className="font-semibold text-foreground text-[11px]">{risk.risk}</span>
                  <p className="text-muted font-sans text-[10px]">{risk.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Catalysts ───────────────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-accent" /> Catalyst Calendar
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {r.catalysts.map((c, i) => (
            <div key={i} className="bg-surface-alt border border-border rounded-lg p-3 space-y-1">
              <div className="flex items-center gap-1.5">
                {c.impact === "Positive" ? <TrendingUp className="w-3.5 h-3.5 text-positive" /> :
                 c.impact === "Negative" ? <TrendingDown className="w-3.5 h-3.5 text-negative" /> :
                 <Minus className="w-3.5 h-3.5 text-accent-yellow" />}
                <span className={`text-[10px] font-bold ${IMPACT_STYLES[c.impact] ?? "text-muted"}`}>{c.impact}</span>
              </div>
              <p className="text-xs font-semibold text-foreground">{c.catalyst}</p>
              <p className="text-[10px] text-muted">{c.timing}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Monitoring Dashboard ─────────────────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-2">
          <Eye className="w-3.5 h-3.5 text-accent" /> Live Thesis Tracker
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-border">
                {["KPI", "Current", "Confirms", "Breaks"].map(h => (
                  <th key={h} className="text-left py-2 px-3 text-muted font-semibold text-[10px] uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {r.monitoringKPIs.map((k, i) => (
                <tr key={i} className="border-b border-border/40 hover:bg-surface-alt">
                  <td className="py-2 px-3 font-bold text-foreground">{k.kpi}</td>
                  <td className="py-2 px-3 text-muted font-mono">{k.current}</td>
                  <td className="py-2 px-3 text-positive font-sans">{k.confirms}</td>
                  <td className="py-2 px-3 text-negative font-sans">{k.breaks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Forensics + Management + Capital Allocation ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[
          { label: "Earnings Quality", icon: <CheckCircle2 className="w-3.5 h-3.5 text-accent" />, text: r.forensicSummary },
          { label: "Management Verdict", icon: <Shield className="w-3.5 h-3.5 text-accent" />, text: r.managementVerdict },
          { label: "Capital Allocation", icon: <TrendingUp className="w-3.5 h-3.5 text-accent" />, text: r.capitalAllocationVerdict },
        ].map(({ label, icon, text }) => (
          <div key={label} className="bg-surface border border-border rounded-xl p-4 space-y-2">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">{icon}{label}</h4>
            <p className="text-xs font-sans text-muted leading-relaxed">{text}</p>
          </div>
        ))}
      </div>

      {/* ── Data Warnings ────────────────────────────────────────────────────── */}
      {r.dataWarnings.length > 0 && (
        <div className="bg-accent-yellow/5 border border-accent-yellow/20 rounded-xl p-4 space-y-2">
          <h4 className="text-[10px] font-bold uppercase tracking-wider text-accent-yellow flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> Evidence Gaps & Data Warnings
          </h4>
          <ul className="space-y-1">
            {r.dataWarnings.map((w, i) => (
              <li key={i} className="text-xs text-accent-yellow/80 font-sans flex items-start gap-1.5">
                <span className="mt-1 w-1 h-1 rounded-full bg-accent-yellow/60 shrink-0" />
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-center text-[10px] text-muted font-sans pb-4">
        Educational research pilot — not investment advice. Analysis generated by AI; verify all figures against primary sources before acting.
      </p>
    </div>
  );
}

function BarChartIcon({ size, className }: { size: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" /><line x1="2" y1="20" x2="22" y2="20" />
    </svg>
  );
}
