"use client";

import type { SignalResearch } from "@/lib/api";

const SIGNAL_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  strong_buy: { label: "Strong Buy", color: "text-emerald-400", bg: "bg-emerald-400/10 border-emerald-400/30" },
  buy: { label: "Buy", color: "text-green-400", bg: "bg-green-400/10 border-green-400/30" },
  hold: { label: "Hold", color: "text-amber-400", bg: "bg-amber-400/10 border-amber-400/30" },
  sell: { label: "Sell", color: "text-orange-400", bg: "bg-orange-400/10 border-orange-400/30" },
  strong_sell: { label: "Strong Sell", color: "text-red-400", bg: "bg-red-400/10 border-red-400/30" },
  no_signal: { label: "No Signal", color: "text-muted", bg: "bg-surface-alt border-border" },
};

const DIMENSIONS: { key: keyof SignalResearch; label: string; desc: string }[] = [
  { key: "quality_score", label: "Quality", desc: "Earnings quality vs peers" },
  { key: "growth_score", label: "Growth", desc: "Revenue/earnings growth vs peers" },
  { key: "financial_health_score", label: "Financial Health", desc: "Leverage & liquidity vs peers" },
  { key: "valuation_score", label: "Valuation", desc: "P/E, P/B attractiveness vs peers" },
  { key: "catalyst_risk_score", label: "Catalyst / Risk", desc: "Macro & sector catalysts" },
  { key: "momentum_score", label: "Momentum", desc: "180-day price return vs peers" },
  { key: "risk_score", label: "Risk (Beta)", desc: "Lower systematic risk scores higher" },
];

function ScoreBar({ score, label }: { score: number | null; label: string }) {
  if (score == null) {
    return (
      <div className="flex items-center gap-3">
        <span className="w-36 shrink-0 text-xs text-muted">{label}</span>
        <span className="text-xs text-muted">—</span>
      </div>
    );
  }
  const pct = Math.min(100, Math.max(0, score));
  const color = score >= 60 ? "#4ade80" : score >= 40 ? "#f59e0b" : "#f87171";
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 shrink-0 text-xs text-foreground">{label}</span>
      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-surface-alt">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="w-8 text-right text-xs tabular-nums" style={{ color }}>{score.toFixed(0)}</span>
    </div>
  );
}

export default function AISignalTab({ signal }: { signal: SignalResearch | null }) {
  if (!signal) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-6 text-center text-sm text-muted">
        Signal data unavailable — run the signal engine against this issuer first.
      </div>
    );
  }

  const cfg = SIGNAL_CONFIG[signal.composite_signal] ?? SIGNAL_CONFIG.no_signal;
  const hasScores = signal.as_of_date != null;

  return (
    <div className="flex flex-col gap-6">
      {/* Composite signal badge */}
      <div className={`rounded-2xl border p-6 ${cfg.bg}`}>
        <div className="mb-1 flex items-center gap-3">
          <span className={`text-3xl font-bold ${cfg.color}`}>{cfg.label}</span>
          {signal.suppressed && (
            <span className="rounded-full bg-red-400/10 px-2 py-0.5 text-xs text-red-400">Suppressed</span>
          )}
        </div>
        {signal.as_of_date && (
          <p className="text-xs text-muted">As of {signal.as_of_date} · Policy v{signal.policy_version}</p>
        )}
        {signal.suppression_reasons && signal.suppression_reasons.length > 0 && (
          <ul className="mt-2 list-inside list-disc text-xs text-muted">
            {signal.suppression_reasons.map((r) => <li key={r}>{r}</li>)}
          </ul>
        )}
        {signal.reason && <p className="mt-2 text-xs text-muted">{signal.reason}</p>}
      </div>

      {/* Dimension scores */}
      {hasScores && (
        <div className="rounded-2xl border border-border bg-surface p-5">
          <h4 className="mb-4 text-sm font-semibold">Dimension Scores (0–100, peer-relative)</h4>
          <div className="flex flex-col gap-3">
            {DIMENSIONS.map(({ key, label, desc }) => (
              <div key={key} title={desc}>
                <ScoreBar score={signal[key] as number | null} label={label} />
              </div>
            ))}
          </div>
          <p className="mt-4 text-[10px] text-muted">
            Each score is peer-relative: 50 = equal to fertilizer sector mean. Scores above 50
            indicate above-average performance on that dimension within the pilot universe.
          </p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="rounded-xl bg-surface-alt p-4">
        <p className="text-xs text-muted">
          <span className="font-medium text-foreground">Internal research only. </span>
          {signal.disclaimer ??
            "Experimental rules-based output for internal research only. Not a regulated investment recommendation."}
        </p>
      </div>
    </div>
  );
}
