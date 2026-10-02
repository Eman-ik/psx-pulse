"use client";

import { API_BASE_URL } from "@/lib/config";
import { useState } from "react";
import { AlertCircle, CheckCircle2, CircleDashed, Loader2, XCircle } from "lucide-react";


type Gate = { name: string; status: "PASS" | "FAIL" | "UNAVAILABLE"; detail: string };
type Result = {
  ticker: string;
  issuer: string;
  last_close: number | null;
  entry_vs_last_close_pct: number | null;
  gates: Gate[];
  position_sizing: {
    risk_budget: number;
    risk_per_share: number;
    shares: number;
    capital_required: number;
    max_loss: number;
    allocation_pct: number;
    reward_risk: { target: number; ratio: number | null }[];
  };
  technical_context: {
    above_20dma: boolean | null;
    above_50dma: boolean | null;
    above_200dma: boolean | null;
    rsi: number | null;
    lookback_high: number;
    lookback_low: number;
    lookback_days: number;
  } | null;
  fundamental_evidence: { level: string; rule: string; facts: number; periods: string[]; sources: string[] };
};

const GATE_LABELS: Record<string, string> = {
  DATA: "Price data",
  TRADE_STRUCTURE: "Trade structure",
  STOP_VS_NOISE: "Stop vs daily noise",
  LIQUIDITY: "Liquidity",
  RISK_BUDGET: "Risk budget",
};

const STATUS_STYLE = {
  PASS: { icon: CheckCircle2, cls: "text-positive" },
  FAIL: { icon: XCircle, cls: "text-negative" },
  UNAVAILABLE: { icon: CircleDashed, cls: "text-muted" },
};

const triState = (v: boolean | null) => (v == null ? "not enough history" : v ? "above" : "below");
const pkr = (v: number) => `PKR ${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

function Field({ label, value, onChange, step = "0.01" }: { label: string; value: string; onChange: (v: string) => void; step?: string }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-muted">{label}</span>
      <input
        type="number"
        inputMode="decimal"
        step={step}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-border bg-surface px-3 py-2 tabular-nums focus:outline-none focus:ring-2 focus:ring-accent"
      />
    </label>
  );
}

export function TradeCheck() {
  const [ticker, setTicker] = useState("FFC");
  const [entry, setEntry] = useState("");
  const [stop, setStop] = useState("");
  const [targets, setTargets] = useState("");
  const [portfolio, setPortfolio] = useState("1000000");
  const [risk, setRisk] = useState("1");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/research/trade/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: ticker.trim().toUpperCase(),
          entry: Number(entry),
          stop: Number(stop),
          targets: targets.split(",").map((t) => Number(t.trim())).filter((t) => t > 0),
          portfolio_value: Number(portfolio),
          risk_percent: Number(risk),
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Check the inputs: every number must be positive.");
      setResult(body);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6">
        <header>
          <h1 className="text-3xl font-bold">Trade check</h1>
          <p className="mt-1 text-sm text-muted">
            Checks a proposed long trade against stored prices and filings. Each check passes or fails on its own;
            there is no combined score or go/no-go verdict.
          </p>
        </header>

        <form onSubmit={submit} className="grid gap-4 rounded-lg border border-border bg-surface p-6 sm:grid-cols-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted">Ticker</span>
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="rounded-lg border border-border bg-surface px-3 py-2 focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </label>
          <Field label="Entry (PKR)" value={entry} onChange={setEntry} />
          <Field label="Stop (PKR)" value={stop} onChange={setStop} />
          <label className="flex flex-col gap-1 text-sm sm:col-span-3">
            <span className="text-muted">Targets (PKR, comma-separated)</span>
            <input
              value={targets}
              onChange={(e) => setTargets(e.target.value)}
              placeholder="e.g. 580, 620"
              className="rounded-lg border border-border bg-surface px-3 py-2 focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </label>
          <Field label="Portfolio value (PKR)" value={portfolio} onChange={setPortfolio} step="1" />
          <Field label="Risk per trade (%)" value={risk} onChange={setRisk} step="0.1" />
          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading || !entry || !stop || !targets}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-5 py-2 text-background hover:opacity-90 disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Run checks
            </button>
          </div>
        </form>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-negative/40 bg-negative/10 p-4 text-sm text-negative">
            <AlertCircle className="h-4 w-4" /> {error}
          </div>
        )}

        {result && (
          <>
            <section className="rounded-lg border border-border bg-surface p-6">
              <h2 className="text-lg font-semibold">
                {result.issuer} ({result.ticker})
              </h2>
              {result.last_close != null && (
                <p className="text-sm text-muted">
                  Last close {pkr(result.last_close)}; your entry is {result.entry_vs_last_close_pct}% from it.
                </p>
              )}
              <ul className="mt-4 divide-y divide-border/50">
                {result.gates.map((g) => {
                  const { icon: Icon, cls } = STATUS_STYLE[g.status];
                  return (
                    <li key={g.name} className="flex gap-3 py-3">
                      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${cls}`} aria-hidden />
                      <div>
                        <p className="font-medium">
                          {GATE_LABELS[g.name] ?? g.name}: <span className={cls}>{g.status}</span>
                        </p>
                        <p className="text-sm text-muted">{g.detail}</p>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>

            <section className="rounded-lg border border-border bg-surface p-6">
              <h2 className="mb-3 text-lg font-semibold">Position sizing</h2>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
                <div><dt className="text-muted">Shares</dt><dd className="font-semibold tabular-nums">{result.position_sizing.shares.toLocaleString()}</dd></div>
                <div><dt className="text-muted">Capital required</dt><dd className="font-semibold tabular-nums">{pkr(result.position_sizing.capital_required)}</dd></div>
                <div><dt className="text-muted">Max loss at stop</dt><dd className="font-semibold tabular-nums">{pkr(result.position_sizing.max_loss)}</dd></div>
                <div><dt className="text-muted">Risk per share</dt><dd className="font-semibold tabular-nums">{pkr(result.position_sizing.risk_per_share)}</dd></div>
                <div><dt className="text-muted">Share of portfolio</dt><dd className="font-semibold tabular-nums">{result.position_sizing.allocation_pct}%</dd></div>
                <div>
                  <dt className="text-muted">Reward/risk by target</dt>
                  <dd className="font-semibold tabular-nums">
                    {result.position_sizing.reward_risk.map((r) => `${r.target}: ${r.ratio ?? "—"}:1`).join(", ")}
                  </dd>
                </div>
              </dl>
            </section>

            <div className="grid gap-6 md:grid-cols-2">
              <section className="rounded-lg border border-border bg-surface p-6 text-sm">
                <h2 className="mb-3 text-lg font-semibold">Technical context</h2>
                {result.technical_context ? (
                  <ul className="space-y-1">
                    <li>20-day average: {triState(result.technical_context.above_20dma)}</li>
                    <li>50-day average: {triState(result.technical_context.above_50dma)}</li>
                    <li>200-day average: {triState(result.technical_context.above_200dma)}</li>
                    <li>RSI (14-day): {result.technical_context.rsi?.toFixed(1) ?? "not enough history"}</li>
                    <li>
                      {result.technical_context.lookback_days}-day range: {pkr(result.technical_context.lookback_low)} to{" "}
                      {pkr(result.technical_context.lookback_high)}
                    </li>
                  </ul>
                ) : (
                  <p className="text-muted">No price on the latest market date for this ticker.</p>
                )}
                <p className="mt-3 text-xs text-muted">Context only; these are not pass/fail checks.</p>
              </section>

              <section className="rounded-lg border border-border bg-surface p-6 text-sm">
                <h2 className="mb-3 text-lg font-semibold">Fundamental evidence: {result.fundamental_evidence.level}</h2>
                {result.fundamental_evidence.facts ? (
                  <>
                    <p>
                      {result.fundamental_evidence.facts} source-linked figures across{" "}
                      {result.fundamental_evidence.periods.length} periods (latest{" "}
                      {result.fundamental_evidence.periods.at(-1)}).
                    </p>
                    <p className="mt-1 text-muted">Source: {result.fundamental_evidence.sources.join("; ")}</p>
                  </>
                ) : (
                  <p>No source-linked financial statements on file.</p>
                )}
                <p className="mt-3 text-xs text-muted">How the level is set: {result.fundamental_evidence.rule}.</p>
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
