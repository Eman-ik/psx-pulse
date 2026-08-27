import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { fetchMlModelEvidence } from "@/lib/api";

function StatCard({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "good" | "bad" | "neutral" }) {
  const color = tone === "good" ? "#22c55e" : tone === "bad" ? "#ef4444" : undefined;
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-muted/70">{label}</p>
      <p className="text-2xl font-bold tabular-nums" style={{ color }}>{value}</p>
      {sub && <p className="mt-1 text-xs text-muted">{sub}</p>}
    </div>
  );
}

export default async function ModelEvidencePage() {
  const evidence = await fetchMlModelEvidence();

  const clearsPrecisionFloor = evidence?.buy_precision != null && evidence.buy_precision >= 0.6;
  const buyPrecisionPasses = clearsPrecisionFloor && evidence?.beats_naive_baseline === true;

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={false} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Model Evidence</h1>
          <p className="mb-6 max-w-3xl text-sm text-muted">
            Out-of-sample validation record for the walk-forward-validated calibrated ML signal
            model (see the &quot;ML Model&quot; tab on any company page). Trained pooled across
            the full PSX universe, not just this sector, so the classifier has enough breadth to
            validate honestly. This page exists so the model&apos;s track record is auditable,
            not just its predictions — a model that hasn&apos;t earned the right to issue a BUY
            should say so, transparently.
          </p>

          {!evidence || evidence.reason ? (
            <p className="text-sm text-muted">
              {evidence?.reason ?? "Model evidence unavailable — backend unreachable."}
            </p>
          ) : (
            <>
              <div
                className="mb-6 rounded-2xl border p-4 text-sm"
                style={
                  buyPrecisionPasses
                    ? { borderColor: "rgba(34,197,94,0.25)", backgroundColor: "rgba(34,197,94,0.08)", color: "#22c55e" }
                    : { borderColor: "rgba(245,158,11,0.25)", backgroundColor: "rgba(245,158,11,0.08)", color: "#f59e0b" }
                }
              >
                {buyPrecisionPasses ? (
                  "Buy precision clears the 60% out-of-sample gate and beats this run's naive baseline — BUY signals are eligible to be issued."
                ) : !clearsPrecisionFloor ? (
                  "Buy precision has not cleared the 60% out-of-sample gate this run — every company shows \"NO SIGNAL\" or \"HOLD\" rather than a fabricated BUY. This is the model working as intended, not a bug."
                ) : (
                  <>
                    Buy precision clears the 60% floor, but doesn&apos;t beat this run&apos;s
                    naive baseline (
                    {evidence.positive_rate != null ? `${(evidence.positive_rate * 100).toFixed(1)}%` : "—"}{" "}
                    of the walk-forward population already beat the benchmark) — a random
                    same-sized subset would score this well by chance, so BUY stays withheld.
                    Same gate that caught Kronos&apos;s EFERT case, one layer down.
                  </>
                )}
              </div>

              <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                <StatCard
                  label="Accuracy"
                  value={evidence.accuracy != null ? `${(evidence.accuracy * 100).toFixed(1)}%` : "—"}
                  sub="vs. 50% coin-flip baseline"
                />
                <StatCard
                  label="Buy Precision"
                  value={evidence.buy_precision != null ? `${(evidence.buy_precision * 100).toFixed(1)}%` : "—"}
                  sub="minimum 60% required to issue BUY"
                  tone={clearsPrecisionFloor ? "good" : "bad"}
                />
                <StatCard
                  label="Naive Baseline"
                  value={evidence.positive_rate != null ? `${(evidence.positive_rate * 100).toFixed(1)}%` : "—"}
                  sub="buy precision must also beat this"
                  tone={evidence.beats_naive_baseline ? "good" : "bad"}
                />
                <StatCard
                  label="Sell Precision"
                  value={evidence.sell_precision != null ? `${(evidence.sell_precision * 100).toFixed(1)}%` : "—"}
                  sub="model never issues SELL (see below)"
                />
                <StatCard
                  label="Brier Score"
                  value={evidence.brier_score != null ? evidence.brier_score.toFixed(4) : "—"}
                  sub="0 = perfect, 0.25 = uninformative"
                />
                <StatCard
                  label="ROC AUC"
                  value={evidence.roc_auc != null ? evidence.roc_auc.toFixed(3) : "—"}
                  sub="0.5 = no skill, 1.0 = perfect"
                />
                <StatCard
                  label="Observations"
                  value={evidence.observations != null ? evidence.observations.toLocaleString() : "—"}
                  sub="out-of-sample walk-forward rows"
                />
                <StatCard
                  label="Model Version"
                  value={evidence.model_version != null ? `v${evidence.model_version}` : "—"}
                />
              </div>

              <div className="rounded-2xl border border-border bg-surface p-5">
                <h2 className="mb-3 text-sm font-semibold">How to read this</h2>
                <ul className="list-inside list-disc space-y-2 text-xs text-muted">
                  <li>
                    <strong className="text-foreground">Accuracy</strong> is the share of
                    out-of-sample 5-day predictions (did the stock beat the market benchmark?)
                    the model got right, across every walk-forward fold.
                  </li>
                  <li>
                    <strong className="text-foreground">Buy precision</strong> is accuracy
                    restricted to the subset of predictions where the model was confident
                    (probability ≥ 60%) — one of two numbers that gate whether a BUY signal is
                    ever issued at all.
                  </li>
                  <li>
                    <strong className="text-foreground">Naive baseline</strong> is the share of
                    the whole walk-forward population that beat the benchmark, regardless of the
                    model&apos;s confidence — what a random, same-sized subset would score by
                    chance. Buy precision must exceed this, not just the fixed 60% floor: a
                    &quot;confident&quot; subset that only matches the population&apos;s own base
                    rate has learned nothing.
                  </li>
                  <li>
                    <strong className="text-foreground">Sell precision</strong> exists for
                    transparency only. The model estimates upside probability, not downside — a
                    low probability is evidence of &quot;no edge detected&quot;, not evidence of
                    a negative return, so SELL is never issued regardless of this number.
                  </li>
                  <li>
                    <strong className="text-foreground">Brier score</strong> and{" "}
                    <strong className="text-foreground">ROC AUC</strong> measure calibration and
                    discrimination quality independent of the 60% threshold — useful for judging
                    whether the model is improving run over run.
                  </li>
                </ul>
                {evidence.calculated_at && (
                  <p className="mt-4 text-[11px] text-muted">
                    Last computed {new Date(evidence.calculated_at).toLocaleString()}
                    {evidence.as_of_date ? ` · data as of ${evidence.as_of_date}` : ""}
                  </p>
                )}
              </div>

              {evidence.disclaimer && (
                <p className="mt-6 text-[11px] text-muted leading-relaxed">{evidence.disclaimer}</p>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
