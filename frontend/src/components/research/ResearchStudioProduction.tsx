"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Loader2, Search } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Freshness = { as_of: string | null; retrieved_at: string | null; sources: string[]; stale: boolean };

type Technical = {
  symbol: string;
  name: string;
  sector: string;
  price: number;
  change_pct: number;
  price_vs_20dma: number;
  price_vs_50dma: number;
  price_vs_200dma: number;
  rsi: number | null;
  volume_vs_avg: number;
  price_near_52week_high: boolean;
  price_near_52week_low: boolean;
};

type Momentum = {
  symbol: string;
  sector: string;
  return_1m: number | null;
  return_3m: number | null;
  return_6m: number | null;
  return_12m: number | null;
};

type Screen<T> = { freshness: Freshness; signals: T[] };

const PERIODS = [
  ["return_1m", "1 month"],
  ["return_3m", "3 months"],
  ["return_6m", "6 months"],
  ["return_12m", "12 months"],
] as const;

const pct = (v: number | null) => (v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`);
const tone = (v: number | null) => (v == null ? "text-muted" : v >= 0 ? "text-positive" : "text-negative");

function trendReading(t: Technical) {
  const above = [t.price_vs_20dma, t.price_vs_50dma, t.price_vs_200dma].filter((v) => v > 0).length;
  if (above === 3) return "Trading above its 20, 50 and 200-day averages.";
  if (above === 0) return "Trading below its 20, 50 and 200-day averages.";
  return `Trading above ${above} of its 20, 50 and 200-day averages.`;
}

function rsiReading(rsi: number | null) {
  if (rsi == null) return "Not enough history to compute.";
  if (rsi >= 70) return "Above 70, conventionally read as overbought.";
  if (rsi <= 30) return "Below 30, conventionally read as oversold.";
  return "Between 30 and 70, the neutral range.";
}

function sectorRank(all: Momentum[], symbol: string, sector: string, key: (typeof PERIODS)[number][0]) {
  const peers = all.filter((m) => m.sector === sector && m[key] != null).sort((a, b) => b[key]! - a[key]!);
  const index = peers.findIndex((m) => m.symbol === symbol);
  return index < 0 ? null : { rank: index + 1, of: peers.length };
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-border bg-surface p-6">
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Row({ label, value, valueClass = "", note }: { label: string; value: string; valueClass?: string; note?: string }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border/50 py-2 last:border-0">
      <span className="text-sm text-muted">{label}</span>
      <span className="text-right">
        <span className={`font-semibold tabular-nums ${valueClass}`}>{value}</span>
        {note && <span className="ml-2 text-xs text-muted">{note}</span>}
      </span>
    </div>
  );
}

export function ResearchStudioProduction() {
  const [query, setQuery] = useState("LUCK");
  const [technical, setTechnical] = useState<Screen<Technical> | null>(null);
  const [momentum, setMomentum] = useState<Screen<Momentum> | null>(null);
  const [symbol, setSymbol] = useState("LUCK");
  const [statementFacts, setStatementFacts] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const get = (path: string) => fetch(`${API}${path}`).then((r) => (r.ok ? r.json() : Promise.reject(r.status)));
    Promise.all([get("/screeners/technical"), get("/screeners/momentum"), get("/data/status")])
      .then(([t, m, status]) => {
        setTechnical(t);
        setMomentum(m);
        setStatementFacts(status.fundamentals.statement_facts);
      })
      .catch(() => setError("Could not reach the research API on port 8000."))
      .finally(() => setLoading(false));
  }, []);

  const t = technical?.signals.find((s) => s.symbol === symbol);
  const m = momentum?.signals.find((s) => s.symbol === symbol);
  const freshness = technical?.freshness;
  const known = technical?.signals.map((s) => s.symbol).sort() ?? [];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/40">
        <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
          <h1 className="mb-4 text-3xl font-bold">Research Studio</h1>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              setSymbol(query.trim().toUpperCase());
            }}
          >
            <input
              value={query}
              onChange={(e) => {
                const value = e.target.value.toUpperCase();
                setQuery(value);
                if (known.includes(value)) setSymbol(value);
              }}
              placeholder="Ticker, e.g. LUCK, FFC, DGKC"
              aria-label="Ticker"
              list="known-symbols"
              className="min-w-0 flex-1 rounded-lg border border-border bg-surface px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent"
            />
            <datalist id="known-symbols">
              {known.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
            <button type="submit" className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2 text-background hover:opacity-90">
              <Search className="h-4 w-4" />
              Open
            </button>
          </form>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6">
        {loading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading market data…
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-negative/40 bg-negative/10 p-4 text-negative">
            <AlertCircle className="h-5 w-5" /> {error}
          </div>
        )}

        {!loading && !error && !t && (
          <div className="rounded-lg border border-border bg-surface p-6">
            <p className="font-semibold">No price history on file for {symbol}.</p>
            <p className="mt-1 text-sm text-muted">Covered tickers: {known.join(", ") || "none yet"}.</p>
          </div>
        )}

        {t && freshness && (
          <>
            {freshness.stale && (
              <div className="flex items-center gap-2 rounded-lg border border-negative/40 bg-negative/10 p-4 text-negative">
                <AlertCircle className="h-5 w-5" />
                Prices are stale: the latest close on file is {freshness.as_of}. Readings below describe that date, not today.
              </div>
            )}

            <section className="rounded-lg border border-border bg-surface p-6">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold">{t.name}</h2>
                  <p className="text-sm text-muted">
                    {t.symbol} · {t.sector}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold tabular-nums">PKR {t.price.toFixed(2)}</p>
                  <p className={`text-sm font-semibold ${tone(t.change_pct)}`}>{pct(t.change_pct)} on the day</p>
                </div>
              </div>
              <p className="mt-4 text-xs text-muted">
                Close as of {freshness.as_of} · source: {freshness.sources.join(", ")} end-of-day (delayed) · retrieved{" "}
                {freshness.retrieved_at ? new Date(freshness.retrieved_at).toLocaleString() : "—"}
              </p>
            </section>

            <div className="grid gap-6 md:grid-cols-2">
              <Section title="Trend">
                <Row label="vs 20-day average" value={pct(t.price_vs_20dma)} valueClass={tone(t.price_vs_20dma)} />
                <Row label="vs 50-day average" value={pct(t.price_vs_50dma)} valueClass={tone(t.price_vs_50dma)} />
                <Row label="vs 200-day average" value={pct(t.price_vs_200dma)} valueClass={tone(t.price_vs_200dma)} />
                <p className="mt-3 text-sm">{trendReading(t)}</p>
              </Section>

              <Section title="Momentum and activity">
                <Row label="RSI (14-day)" value={t.rsi == null ? "—" : t.rsi.toFixed(1)} />
                <p className="mb-3 text-sm">{rsiReading(t.rsi)}</p>
                <Row label="Volume vs 20-day average" value={`${t.volume_vs_avg.toFixed(2)}×`} />
                <Row
                  label="52-week range"
                  value={t.price_near_52week_high ? "Within 5% of high" : t.price_near_52week_low ? "Within 5% of low" : "Mid-range"}
                />
              </Section>
            </div>

            {m && momentum && (
              <Section title={`Price returns vs ${t.sector} peers`}>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-muted">
                        <th className="py-2 font-medium">Period</th>
                        <th className="py-2 text-right font-medium">Return</th>
                        <th className="py-2 text-right font-medium">Rank in sector</th>
                      </tr>
                    </thead>
                    <tbody>
                      {PERIODS.map(([key, label]) => {
                        const rank = sectorRank(momentum.signals, t.symbol, t.sector, key);
                        return (
                          <tr key={key} className="border-t border-border/50">
                            <td className="py-2">{label}</td>
                            <td className={`py-2 text-right font-semibold tabular-nums ${tone(m[key])}`}>{pct(m[key])}</td>
                            <td className="py-2 text-right tabular-nums">{rank ? `${rank.rank} of ${rank.of}` : "—"}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <p className="mt-3 text-xs text-muted">
                  Unadjusted closes: dividends and bonus issues are not included, so total return can be higher.
                </p>
              </Section>
            )}

            <Section title="Fundamentals">
              <p className="text-sm">
                {statementFacts
                  ? `Statements are on file for some companies, but this view doesn't show them yet.`
                  : `No source-linked financial statements are on file for any company yet.`}
              </p>
              <p className="mt-1 text-sm text-muted">
                Valuation, profitability and balance-sheet analysis appear here once statements are loaded with a link to the
                filing they came from.
              </p>
            </Section>

            <p className="text-xs text-muted">
              Readings use fixed, conventional thresholds and describe the data. They are not recommendations.
            </p>
          </>
        )}
      </main>
    </div>
  );
}
