import type { MlSignalResearch } from "@/lib/api";

const SIGNAL_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  BUY:        { label: "Buy",        color: "#22c55e", bg: "rgba(34,197,94,0.08)",   border: "rgba(34,197,94,0.25)" },
  HOLD:       { label: "Hold",       color: "#f59e0b", bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.25)" },
  "NO SIGNAL":{ label: "No Signal",  color: "#6b7280", bg: "rgba(107,114,128,0.06)", border: "rgba(107,114,128,0.20)" },
};

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl bg-surface-alt p-4">
      <p className="mb-1 text-xs text-muted">{label}</p>
      <p className="text-lg font-bold tabular-nums">{value}</p>
      {sub && <p className="mt-1 text-[10px] text-muted">{sub}</p>}
    </div>
  );
}

export default function MLModelTab({ signal }: { signal: MlSignalResearch | null }) {
  if (!signal) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-5">
        <p className="text-sm text-muted">ML model data unavailable — backend unreachable.</p>
      </div>
    );
  }

  const meta = SIGNAL_META[signal.signal] ?? SIGNAL_META["NO SIGNAL"];
  const accuracyPasses = signal.validation_accuracy != null && signal.validation_accuracy >= 0.5;
  const clearsPrecisionFloor = signal.validation_buy_precision != null && signal.validation_buy_precision >= 0.6;
  const clearsNaiveBaseline = clearsPrecisionFloor && signal.beats_naive_baseline === true;
  const buyPrecisionPasses = clearsNaiveBaseline && signal.significant_at_10pct === true;
  const precisionSub = !clearsPrecisionFloor
    ? "below 60% gate — BUY withheld"
    : !clearsNaiveBaseline
      ? "clears 60% but not naive baseline — BUY withheld"
      : buyPrecisionPasses
        ? "clears 60% + naive baseline + significant"
        : "clears 60% + naive baseline but not significant — BUY withheld";

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-2xl border border-border bg-surface p-5">
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-muted/70">
          Walk-Forward Validated ML Model
        </p>
        <p className="mb-4 text-xs text-muted">
          A calibrated logistic regression trained on price/volume-derived features, pooled
          across the full PSX universe and out-of-sample validated with a walk-forward
          methodology (not backtested on its own training data). Experimental — kept separate
          from this company&apos;s rules-based AI Signal above.
        </p>

        {signal.reason ? (
          <p className="text-sm text-muted">{signal.reason}</p>
        ) : (
          <>
            <div className="mb-4 flex flex-wrap items-center gap-4">
              <div className="rounded-2xl border px-4 py-3" style={{ backgroundColor: meta.bg, borderColor: meta.border }}>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted/70">Model Signal</p>
                <p className="text-2xl font-bold" style={{ color: meta.color }}>{meta.label}</p>
              </div>
              {signal.outperformance_probability != null && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted/70">
                    5-Day Outperformance Probability
                  </p>
                  <p className="text-2xl font-bold tabular-nums">
                    {(signal.outperformance_probability * 100).toFixed(1)}%
                  </p>
                </div>
              )}
              {signal.as_of_date && (
                <p className="text-xs text-muted">As of {signal.as_of_date}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Stat
                label="Validated Accuracy"
                value={signal.validation_accuracy != null ? `${(signal.validation_accuracy * 100).toFixed(1)}%` : "—"}
                sub={accuracyPasses ? undefined : "below coin-flip baseline"}
              />
              <Stat
                label="Buy Precision (OOS)"
                value={signal.validation_buy_precision != null ? `${(signal.validation_buy_precision * 100).toFixed(1)}%` : "—"}
                sub={precisionSub}
              />
              <Stat
                label="Naive Baseline"
                value={signal.validation_positive_rate != null ? `${(signal.validation_positive_rate * 100).toFixed(1)}%` : "—"}
                sub="buy precision must also beat this"
              />
              <Stat
                label="Significance (p-value)"
                value={signal.validation_p_value != null ? signal.validation_p_value.toPrecision(3) : "—"}
                sub="must be < 0.10 to issue BUY"
              />
              <Stat
                label="Brier Score"
                value={signal.validation_brier_score != null ? signal.validation_brier_score.toFixed(4) : "—"}
                sub="lower is better"
              />
              <Stat
                label="ROC AUC"
                value={signal.validation_roc_auc != null ? signal.validation_roc_auc.toFixed(3) : "—"}
                sub="0.5 = no skill"
              />
            </div>

            {signal.validation_observations != null && (
              <p className="mt-4 text-[11px] text-muted">
                Validated on {signal.validation_observations.toLocaleString()} out-of-sample
                walk-forward observations, pooled across the full PSX universe (not just this
                sector) so the classifier has enough breadth to validate honestly.
              </p>
            )}
          </>
        )}
      </div>

      {signal.disclaimer && (
        <p className="text-[11px] text-muted leading-relaxed">{signal.disclaimer}</p>
      )}
    </div>
  );
}
