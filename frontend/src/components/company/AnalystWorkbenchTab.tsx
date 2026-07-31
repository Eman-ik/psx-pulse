"use client";

import { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Legend,
} from "recharts";
import type { AnalystRunResult, ForensicsData, CAPMDiagnosticsData } from "@/lib/api";
import { fetchAnalystRun, triggerAnalystRun, fetchForensics, fetchCAPMDiagnostics } from "@/lib/api";

const HEALTH_COLOR: Record<string, string> = {
  genuinely_healthy: "text-green-400",
  healthy_but_cyclical: "text-teal-400",
  improving: "text-blue-400",
  surface_level_strength: "text-yellow-400",
  deteriorating: "text-orange-400",
  financially_fragile: "text-red-400",
  insufficient_evidence: "text-muted",
};

const STANCE_COLOR: Record<string, string> = {
  positive: "bg-green-900/40 border-green-600 text-green-300",
  neutral: "bg-zinc-800 border-border text-foreground",
  negative: "bg-red-900/40 border-red-600 text-red-300",
  watch: "bg-yellow-900/40 border-yellow-600 text-yellow-300",
  insufficient_evidence: "bg-zinc-800/50 border-border text-muted",
};

const FLAG_SEVERITY_COLOR: Record<string, string> = {
  low: "text-blue-400",
  medium: "text-yellow-400",
  high: "text-orange-400",
  critical: "text-red-400",
};

const FLAG_STATUS_ICON: Record<string, string> = {
  clear: "✓",
  watch: "⚠",
  triggered: "✗",
  not_applicable: "–",
  insufficient_data: "?",
};

function ScoreBar({ label, value, tooltip }: { label: string; value: number | null; tooltip?: string }) {
  if (value === null) {
    return (
      <div className="flex items-center gap-3">
        <span className="w-40 text-xs text-muted" title={tooltip}>{label}</span>
        <span className="text-xs text-muted italic">Insufficient data</span>
      </div>
    );
  }
  const color = value >= 65 ? "bg-green-500" : value >= 40 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-3" title={tooltip}>
      <span className="w-40 text-xs text-muted">{label}</span>
      <div className="flex-1 rounded-full bg-zinc-700 h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="w-8 text-right text-xs font-mono text-foreground">{Math.round(value)}</span>
    </div>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-3">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {subtitle && <p className="text-xs text-muted mt-0.5">{subtitle}</p>}
    </div>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg border border-border bg-surface p-4 ${className}`}>
      {children}
    </div>
  );
}

function ForensicFlagsPanel({ flags }: { flags: ForensicsData["flags"] }) {
  return (
    <div className="space-y-2">
      {flags.map((flag) => (
        <div key={flag.flag_code} className="rounded border border-border bg-bg p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <span
                className={`text-sm font-bold ${FLAG_SEVERITY_COLOR[flag.severity] ?? "text-muted"}`}
                title={`Severity: ${flag.severity}`}
              >
                {FLAG_STATUS_ICON[flag.status] ?? "?"}
              </span>
              <span className="text-xs font-mono text-foreground">{flag.flag_code}</span>
              <span className={`text-[10px] uppercase tracking-wide ${FLAG_SEVERITY_COLOR[flag.severity] ?? "text-muted"}`}>
                {flag.severity}
              </span>
            </div>
            <span className="text-[10px] text-muted capitalize">{flag.status.replace("_", " ")}</span>
          </div>
          <p className="mt-1 text-xs text-muted leading-relaxed">{flag.explanation}</p>
          {flag.observed_value && (
            <p className="mt-1 text-[10px] text-muted">
              Observed: <span className="font-mono text-foreground">{flag.observed_value}</span>
              {flag.sector_reference && (
                <> · Ref: <span className="font-mono">{flag.sector_reference}</span></>
              )}
            </p>
          )}
          {flag.possible_benign_explanations.length > 0 && (
            <p className="mt-1 text-[10px] text-muted italic">
              Possible benign: {flag.possible_benign_explanations.join("; ")}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function DuPontTable({ dupont }: { dupont: ForensicsData["dupont"] }) {
  if (!dupont.length) return <p className="text-xs text-muted">No data.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border text-muted">
            <th className="py-1.5 text-left font-normal">Period</th>
            <th className="py-1.5 text-right font-normal">Net Margin %</th>
            <th className="py-1.5 text-right font-normal">Asset Turnover</th>
            <th className="py-1.5 text-right font-normal">Equity Mult.</th>
            <th className="py-1.5 text-right font-normal">ROE (3-way) %</th>
            <th className="py-1.5 text-right font-normal">ROE (reported)</th>
          </tr>
        </thead>
        <tbody>
          {dupont.map((row) => (
            <tr key={row.period_end} className="border-b border-border/40 hover:bg-zinc-800/30">
              <td className="py-1.5 font-mono">{row.period_end.slice(0, 4)}</td>
              <td className="py-1.5 text-right font-mono">{row.net_margin ?? "–"}</td>
              <td className="py-1.5 text-right font-mono">{row.asset_turnover ?? "–"}</td>
              <td className="py-1.5 text-right font-mono">{row.equity_multiplier ?? "–"}</td>
              <td className="py-1.5 text-right font-mono font-semibold">{row.roe_3way ?? "–"}</td>
              <td className="py-1.5 text-right font-mono text-muted">{row.roe_reported?.toFixed(1) ?? "–"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1.5 text-[10px] text-muted">
        ROE = Net Margin × Asset Turnover × Equity Multiplier (3-way DuPont). Reported = ratio_engine calculation.
      </p>
    </div>
  );
}

function CFOPATChart({ cashConversion }: { cashConversion: ForensicsData["cash_conversion"] }) {
  if (!cashConversion.length) return <p className="text-xs text-muted">No data.</p>;
  const hasAnyRatio = cashConversion.some((r) => r.cfo_pat_ratio !== null);
  const chartData = cashConversion.map((r) => ({
    year: r.period_end.slice(0, 4),
    pat: r.profit_after_tax / 1000,
    cfo: r.operating_cash_flow != null ? r.operating_cash_flow / 1000 : null,
    ratio: r.cfo_pat_ratio,
  }));

  if (!hasAnyRatio) {
    return (
      <div>
        <p className="text-xs text-muted mb-2">Operating cash flow not on file — showing PAT only.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-border text-muted">
              <th className="py-1 text-left font-normal">Period</th>
              <th className="py-1 text-right font-normal">PAT (PKR mn)</th>
            </tr></thead>
            <tbody>
              {chartData.map((r) => (
                <tr key={r.year} className="border-b border-border/40">
                  <td className="py-1 font-mono">{r.year}</td>
                  <td className="py-1 text-right font-mono">{r.pat.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="year" tick={{ fontSize: 10, fill: "var(--color-muted)" }} />
            <YAxis tick={{ fontSize: 10, fill: "var(--color-muted)" }} unit=" mn" />
            <Tooltip
              contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6 }}
              labelStyle={{ color: "var(--color-muted)", fontSize: 10 }}
              itemStyle={{ fontSize: 11 }}
            />
            <Bar dataKey="pat" name="PAT" fill="#6366f1" radius={[3, 3, 0, 0]} />
            <Bar dataKey="cfo" name="CFO" fill="#22c55e" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex items-center gap-4 text-[10px] text-muted">
        <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded bg-[#6366f1]" /> PAT (PKR mn)</span>
        <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded bg-[#22c55e]" /> CFO (PKR mn)</span>
      </div>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="border-b border-border text-muted">
            <th className="py-1 text-left font-normal">Period</th>
            <th className="py-1 text-right font-normal">CFO/PAT ratio</th>
            <th className="py-1 text-right font-normal">Status</th>
          </tr></thead>
          <tbody>
            {cashConversion.map((r) => (
              <tr key={r.period_end} className="border-b border-border/40">
                <td className="py-1 font-mono">{r.period_end.slice(0, 4)}</td>
                <td className={`py-1 text-right font-mono font-semibold ${
                  r.cfo_pat_ratio == null ? "text-muted" :
                  r.cfo_pat_ratio >= 0.85 ? "text-green-400" :
                  r.cfo_pat_ratio >= 0.65 ? "text-yellow-400" : "text-red-400"
                }`}>
                  {r.cfo_pat_ratio != null ? `${r.cfo_pat_ratio}x` : "n/a"}
                </td>
                <td className="py-1 text-right text-muted">
                  {r.cfo_pat_ratio == null ? "–" :
                   r.cfo_pat_ratio >= 0.85 ? "Good" :
                   r.cfo_pat_ratio >= 0.65 ? "Watch" : "Low"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-1 text-[10px] text-muted">CFO/PAT ≥ 0.85 = good quality. &lt;0.65 = earnings-quality concern.</p>
    </div>
  );
}

function CAPMPanel({ capm }: { capm: CAPMDiagnosticsData }) {
  const confColor = capm.confidence === "high" ? "text-green-400" : capm.confidence === "medium" ? "text-yellow-400" : "text-red-400";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Beta", val: capm.beta?.toFixed(3) ?? "–" },
          { label: "R²", val: capm.r_squared?.toFixed(3) ?? "–" },
          { label: "t-stat", val: capm.beta_t_stat?.toFixed(2) ?? "–" },
          { label: "p-value", val: capm.beta_p_value?.toFixed(4) ?? "–" },
        ].map(({ label, val }) => (
          <div key={label} className="rounded border border-border bg-bg p-2 text-center">
            <div className="text-[10px] text-muted">{label}</div>
            <div className="mt-0.5 font-mono text-sm text-foreground">{val}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {[
          { label: "Required Return", val: capm.required_return_pct != null ? `${capm.required_return_pct}%` : "–" },
          { label: "95% CI (beta)", val: (capm.beta_ci_low != null && capm.beta_ci_high != null) ? `[${capm.beta_ci_low}, ${capm.beta_ci_high}]` : "–" },
          { label: "Annualised Alpha", val: capm.alpha_annualised != null ? `${capm.alpha_annualised}%` : "–" },
        ].map(({ label, val }) => (
          <div key={label} className="rounded border border-border bg-bg p-2">
            <div className="text-[10px] text-muted">{label}</div>
            <div className="mt-0.5 font-mono text-xs text-foreground">{val}</div>
          </div>
        ))}
      </div>
      {(capm.up_market_beta != null || capm.down_market_beta != null) && (
        <div className="rounded border border-border bg-bg p-3">
          <p className="text-xs text-muted mb-1">Asymmetric beta</p>
          <div className="flex gap-6">
            <span className="text-xs">Up-market: <span className="font-mono text-foreground">{capm.up_market_beta ?? "–"}</span></span>
            <span className="text-xs">Down-market: <span className="font-mono text-foreground">{capm.down_market_beta ?? "–"}</span></span>
          </div>
          {capm.asymmetry_note && <p className="mt-1 text-xs text-muted italic">{capm.asymmetry_note}</p>}
        </div>
      )}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted">Confidence:</span>
        <span className={`text-xs font-semibold capitalize ${confColor}`}>{capm.confidence}</span>
        {capm.stale_price_warning && (
          <span className="text-[10px] text-yellow-400">⚠ stale-price warning</span>
        )}
      </div>
      {capm.confidence_notes.length > 0 && (
        <ul className="space-y-0.5">
          {capm.confidence_notes.map((n, i) => (
            <li key={i} className="text-[10px] text-muted">• {n}</li>
          ))}
        </ul>
      )}
      {capm.rolling_beta.length > 0 && (
        <div>
          <p className="text-[10px] text-muted mb-1.5">Rolling 52-week beta</p>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={capm.rolling_beta.map((r) => ({ date: r.window_end.slice(0, 7), beta: r.beta }))} margin={{ top: 2, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: "var(--color-muted)" }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 9, fill: "var(--color-muted)" }} domain={["auto", "auto"]} />
                <Tooltip contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, fontSize: 10 }} />
                <ReferenceLine y={1} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="beta" stroke="var(--color-accent)" strokeWidth={1.5} dot={false} name="Rolling Beta" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      <p className="text-[10px] text-muted">
        CAPM estimates market-risk required return only. Not a prediction of price direction (Blueprint §7.5).
        Required return uses R_f={capm.risk_free_rate_pct}% + β × ERP {capm.erp_pct}%.
      </p>
    </div>
  );
}

function ThesisSection({ packet }: { packet: Record<string, unknown> }) {
  const scenarios = packet.scenarios as Record<string, { title: string; narrative: string; key_driver: string }> | undefined;
  const catalysts = packet.catalysts as { catalyst: string; timeframe: string; probability: string }[] | undefined;
  const risks = packet.risks as { risk: string; severity: string; probability: string }[] | undefined;
  const findings = packet.key_findings as { finding: string; direction: string; materiality: string }[] | undefined;

  if (!scenarios && !catalysts && !risks) {
    return (
      <div className="rounded border border-border bg-bg p-4 text-center">
        <p className="text-xs text-muted">LLM synthesis not yet run or API key not configured.</p>
        <p className="mt-1 text-[10px] text-muted">
          Set <span className="font-mono">ANTHROPIC_API_KEY</span> in <span className="font-mono">backend/.env</span> and re-run the analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {findings && findings.length > 0 && (
        <div>
          <SectionHeader title="Key Findings" />
          <div className="space-y-1.5">
            {findings.map((f, i) => (
              <div key={i} className={`flex items-start gap-2 rounded border p-2 text-xs ${
                f.direction === "positive" ? "border-green-900 bg-green-900/20" :
                f.direction === "negative" ? "border-red-900 bg-red-900/20" :
                "border-border bg-bg"
              }`}>
                <span className="mt-0.5 text-sm">{f.direction === "positive" ? "↑" : f.direction === "negative" ? "↓" : "~"}</span>
                <div>
                  <span className="text-foreground">{f.finding}</span>
                  <span className="ml-2 text-[10px] uppercase text-muted">{f.materiality}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {scenarios && (
        <div>
          <SectionHeader title="Scenarios" />
          <div className="grid gap-3 sm:grid-cols-3">
            {(["bull", "base", "bear"] as const).map((s) => {
              const sc = scenarios[s];
              if (!sc) return null;
              const colors = { bull: "border-green-800 bg-green-900/20", base: "border-border bg-bg", bear: "border-red-800 bg-red-900/20" };
              return (
                <div key={s} className={`rounded border p-3 ${colors[s]}`}>
                  <p className="text-[10px] uppercase tracking-wide text-muted mb-1 capitalize">{s}</p>
                  <p className="text-xs font-medium text-foreground">{sc.title}</p>
                  <p className="mt-1.5 text-[11px] text-muted leading-relaxed">{sc.narrative}</p>
                  {sc.key_driver && (
                    <p className="mt-1.5 text-[10px] text-muted">Key driver: <span className="italic">{sc.key_driver}</span></p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {catalysts && catalysts.length > 0 && (
          <div>
            <SectionHeader title="Catalysts" />
            <div className="space-y-1.5">
              {catalysts.map((c, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className="mt-0.5 text-green-400">▲</span>
                  <div>
                    <span className="text-foreground">{c.catalyst}</span>
                    <span className="ml-2 text-[10px] text-muted capitalize">{c.timeframe?.replace("_", "-")} · {c.probability}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        {risks && risks.length > 0 && (
          <div>
            <SectionHeader title="Risks" />
            <div className="space-y-1.5">
              {risks.map((r, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className={`mt-0.5 ${r.severity === "high" || r.severity === "critical" ? "text-red-400" : "text-yellow-400"}`}>▼</span>
                  <div>
                    <span className="text-foreground">{r.risk}</span>
                    <span className="ml-2 text-[10px] text-muted capitalize">{r.severity} · {r.probability}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AnalystWorkbenchTab({ issuerId }: { issuerId: number }) {
  const [run, setRun] = useState<AnalystRunResult | null>(null);
  const [forensics, setForensics] = useState<ForensicsData | null>(null);
  const [capm, setCAPM] = useState<CAPMDiagnosticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [activeSection, setActiveSection] = useState<"overview" | "forensics" | "capm" | "thesis">("overview");

  const loadData = useCallback(async () => {
    const [runRes, forensicsRes, capmRes] = await Promise.all([
      fetchAnalystRun(issuerId),
      fetchForensics(issuerId),
      fetchCAPMDiagnostics(issuerId),
    ]);
    setRun(runRes);
    setForensics(forensicsRes);
    setCAPM(capmRes);
    setLoading(false);
  }, [issuerId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunAnalysis = async () => {
    setRunning(true);
    const result = await triggerAnalystRun(issuerId);
    setRunning(false);
    if (result) {
      await loadData();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-sm text-muted">
        Loading analyst data…
      </div>
    );
  }

  const packet = run?.packet?.packet_json as Record<string, unknown> | undefined;
  const posture = run?.packet;
  const hasPacket = posture && packet;
  const forensicData = (packet?.forensics ?? null) as Record<string, unknown> | null;
  const capmData = (packet?.capm ?? null) as Record<string, unknown> | null;

  const SECTIONS = [
    { key: "overview", label: "Overview" },
    { key: "forensics", label: "Forensics" },
    { key: "capm", label: "CAPM & Risk" },
    { key: "thesis", label: "Thesis" },
  ] as const;

  return (
    <div className="space-y-5">
      {/* Disclaimer */}
      <div className="rounded border border-yellow-900/50 bg-yellow-900/10 px-3 py-2 text-[10px] text-yellow-300/80">
        Internal research only · Not a regulated investment recommendation · All numbers from deterministic models · LLM interprets evidence, does not calculate · See docs/research_disclaimer.md
      </div>

      {/* Header: Run button + posture */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          {hasPacket ? (
            <div className="space-y-1.5">
              <div className={`inline-flex items-center gap-2 rounded border px-3 py-1.5 text-sm font-semibold ${STANCE_COLOR[posture.research_posture] ?? STANCE_COLOR.insufficient_evidence}`}>
                <span className="uppercase tracking-wide text-xs">{posture.research_posture.replace("_", " ")}</span>
                <span className="text-[10px] opacity-70">· {posture.confidence} confidence</span>
              </div>
              {posture.one_sentence_view && (
                <p className="max-w-xl text-sm text-foreground leading-relaxed">{posture.one_sentence_view}</p>
              )}
              {posture.decision_hinge && (
                <p className="text-xs text-muted">Key question: <em>{posture.decision_hinge}</em></p>
              )}
            </div>
          ) : (
            <div>
              <p className="text-sm text-muted">No analyst run on file for this company.</p>
              <p className="mt-0.5 text-xs text-muted">Run the analysis to generate a full forensic assessment and AI-powered thesis.</p>
            </div>
          )}
        </div>

        <div className="flex flex-col items-end gap-1.5">
          <button
            onClick={handleRunAnalysis}
            disabled={running}
            className="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {running ? "Running analysis…" : hasPacket ? "Re-run Analysis" : "Run Analysis"}
          </button>
          {running && (
            <p className="text-[10px] text-muted">This may take 30–60 seconds…</p>
          )}
          {hasPacket && run?.completed_at && (
            <p className="text-[10px] text-muted">Last run: {new Date(run.completed_at).toLocaleDateString()}</p>
          )}
        </div>
      </div>

      {/* Business health + sub-scores (always shown from deterministic forensics) */}
      {forensics && (
        <Card>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-[10px] text-muted uppercase tracking-wide mb-1">Business Health</p>
              <p className={`text-base font-semibold capitalize ${HEALTH_COLOR[forensics.business_health] ?? "text-foreground"}`}>
                {forensics.business_health.replace(/_/g, " ")}
              </p>
              <p className="text-[10px] text-muted mt-0.5">
                Confidence: {forensics.health_confidence} · Data coverage: {forensics.data_coverage_pct}%
              </p>
            </div>
            <div className="flex-1 min-w-[200px] space-y-2">
              <ScoreBar label="Operating Health" value={forensics.sub_scores.operating_health} tooltip="Revenue/margin trend and interest coverage" />
              <ScoreBar label="Earnings Quality" value={forensics.sub_scores.earnings_quality} tooltip="CFO/PAT cash conversion ratio" />
              <ScoreBar label="Balance Sheet" value={forensics.sub_scores.balance_sheet} tooltip="Leverage and liquidity ratios" />
              <ScoreBar label="Capital Allocation" value={forensics.sub_scores.capital_allocation} tooltip="ROE trend and sustainability" />
              <ScoreBar label="Governance" value={forensics.sub_scores.governance} tooltip="Insufficient data in pilot" />
            </div>
          </div>
          {forensics.missing_data_items.length > 0 && (
            <p className="mt-3 text-[10px] text-muted border-t border-border pt-2">
              Missing line items: <span className="font-mono">{forensics.missing_data_items.join(", ")}</span>
            </p>
          )}
        </Card>
      )}

      {/* Section tabs */}
      <div className="flex flex-wrap gap-1 border-b border-border">
        {SECTIONS.map((s) => (
          <button
            key={s.key}
            onClick={() => setActiveSection(s.key)}
            className={`px-3 py-2 text-xs font-medium rounded-t transition-colors ${
              activeSection === s.key
                ? "border-b-2 border-accent text-accent"
                : "text-muted hover:text-foreground"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Overview section */}
      {activeSection === "overview" && capm && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <p className="text-[10px] text-muted mb-2">CAPM Beta</p>
            <p className="text-2xl font-mono font-bold text-foreground">
              {capm.beta?.toFixed(3) ?? "–"}
            </p>
            <p className="text-[10px] text-muted mt-0.5">
              t={capm.beta_t_stat?.toFixed(2) ?? "–"} · R²={capm.r_squared?.toFixed(3) ?? "–"}
            </p>
            <p className="text-[10px] text-muted">95% CI: [{capm.beta_ci_low?.toFixed(3) ?? "–"}, {capm.beta_ci_high?.toFixed(3) ?? "–"}]</p>
          </Card>
          <Card>
            <p className="text-[10px] text-muted mb-2">Required Return (CAPM)</p>
            <p className="text-2xl font-mono font-bold text-foreground">
              {capm.required_return_pct != null ? `${capm.required_return_pct}%` : "–"}
            </p>
            <p className="text-[10px] text-muted mt-0.5">
              Low: {capm.required_return_low_pct ?? "–"}% · High: {capm.required_return_high_pct ?? "–"}%
            </p>
            <p className="text-[10px] text-muted">R_f={capm.risk_free_rate_pct}% + β × ERP {capm.erp_pct}%</p>
          </Card>
          {forensics && (
            <Card>
              <p className="text-[10px] text-muted mb-2">Data Coverage</p>
              <p className="text-2xl font-mono font-bold text-foreground">{forensics.data_coverage_pct}%</p>
              <p className="text-[10px] text-muted mt-0.5">of key line items on file</p>
              <p className="text-[10px] text-muted">{forensics.missing_data_items.length} items missing</p>
            </Card>
          )}
        </div>
      )}

      {/* Forensics section */}
      {activeSection === "forensics" && forensics && (
        <div className="space-y-5">
          <Card>
            <SectionHeader title="DuPont ROE Decomposition" subtitle="ROE = Net Margin × Asset Turnover × Equity Multiplier" />
            <DuPontTable dupont={forensics.dupont} />
          </Card>
          <Card>
            <SectionHeader title="Cash Flow vs Reported Profit (CFO/PAT)" subtitle="Measures earnings quality — how much reported profit converts to operating cash" />
            <CFOPATChart cashConversion={forensics.cash_conversion} />
          </Card>
          {forensics.interest_coverage.length > 0 && (
            <Card>
              <SectionHeader title="Interest Coverage" subtitle="EBIT proxy / Finance cost" />
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b border-border text-muted">
                    <th className="py-1 text-left font-normal">Period</th>
                    <th className="py-1 text-right font-normal">EBIT proxy (PKR '000)</th>
                    <th className="py-1 text-right font-normal">Finance Cost</th>
                    <th className="py-1 text-right font-normal">Coverage</th>
                  </tr></thead>
                  <tbody>
                    {forensics.interest_coverage.map((r) => (
                      <tr key={r.period_end} className="border-b border-border/40">
                        <td className="py-1 font-mono">{r.period_end.slice(0, 4)}</td>
                        <td className="py-1 text-right font-mono">{r.ebit_proxy?.toLocaleString() ?? "–"}</td>
                        <td className="py-1 text-right font-mono">{r.finance_cost?.toLocaleString() ?? "–"}</td>
                        <td className={`py-1 text-right font-mono font-semibold ${
                          r.coverage == null ? "text-muted" : r.coverage >= 3 ? "text-green-400" : r.coverage >= 1.5 ? "text-yellow-400" : "text-red-400"
                        }`}>
                          {r.coverage != null ? `${r.coverage}x` : "–"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
          <Card>
            <SectionHeader title="Forensic Flags" subtitle="Deterministic accounting-quality tests. Flags are observations, not accusations." />
            <ForensicFlagsPanel flags={forensics.flags} />
          </Card>
        </div>
      )}

      {/* CAPM & Risk section */}
      {activeSection === "capm" && (
        <div className="space-y-4">
          {capm ? (
            <Card>
              <SectionHeader title="CAPM Diagnostics" subtitle={`Window: ${capm.window_label} · Benchmark: ${capm.benchmark}`} />
              <CAPMPanel capm={capm} />
            </Card>
          ) : (
            <Card>
              <p className="text-xs text-muted">Insufficient price history for CAPM estimation.</p>
            </Card>
          )}
          {hasPacket && packet?.factor_model != null && (
            <Card>
              <SectionHeader
                title="Factor Exposure Model"
                subtitle="Multi-factor OLS — NOT an APT expected-return model (no cross-sectional premia estimated)"
              />
              <div className="space-y-2">
                {((packet.factor_model as Record<string, unknown>).factors as Array<{
                  factor_name: string; beta: number | null; t_stat: number | null; p_value: number | null; interpretation: string; data_available: boolean
                }> ?? []).map((f) => (
                  <div key={f.factor_name} className={`rounded border p-2.5 ${f.data_available ? "border-border bg-bg" : "border-border/30 bg-bg/30"}`}>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-foreground capitalize">{f.factor_name} factor</span>
                      {f.beta != null && (
                        <span className="font-mono text-xs text-foreground">β = {f.beta}</span>
                      )}
                    </div>
                    {f.t_stat != null && (
                      <span className="text-[10px] text-muted">t={f.t_stat} · p={f.p_value}</span>
                    )}
                    <p className="mt-0.5 text-[11px] text-muted">{f.interpretation}</p>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-[10px] text-muted border-t border-border pt-2">
                Model classification: <span className="font-mono">{String((packet.factor_model as Record<string, unknown>).model_classification)}</span> ·
                APT status: <span className="font-mono">{String((packet.factor_model as Record<string, unknown>).apt_expected_return_status)}</span>
              </p>
            </Card>
          )}
        </div>
      )}

      {/* Thesis section */}
      {activeSection === "thesis" && (
        <Card>
          <SectionHeader title="AI-Generated Thesis" subtitle="Interpretation by PSX Senior Analyst Agent — not a regulated recommendation" />
          {hasPacket ? (
            <ThesisSection packet={packet} />
          ) : (
            <div className="text-center py-6">
              <p className="text-sm text-muted">Run the analysis to generate an AI-powered thesis.</p>
              <button
                onClick={handleRunAnalysis}
                disabled={running}
                className="mt-3 rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
              >
                {running ? "Running…" : "Run Analysis"}
              </button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
